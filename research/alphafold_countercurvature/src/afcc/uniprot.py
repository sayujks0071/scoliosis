import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

UNIPROT_API_URL = "https://rest.uniprot.org/idmapping"
POLLING_INTERVAL = 5
MAX_RETRIES = 20

class UniProtMapper:
    def __init__(self, dry_run: bool = False, cache_path: Optional[Path] = None):
        self.dry_run = dry_run
        self.cache_path = cache_path
        self.cache = self._load_cache()

    def _load_cache(self) -> pd.DataFrame:
        if self.cache_path and self.cache_path.exists():
            try:
                df = pd.read_csv(self.cache_path)
                df['gene_symbol'] = df['gene_symbol'].astype(str)
                return df
            except Exception as e:
                print(f"⚠️ Failed to load cache: {e}")
        return pd.DataFrame(columns=['gene_symbol', 'uniprot_accession', 'organism_id', 'status', 'retrieved_at'])

    def _save_cache(self):
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache.to_csv(self.cache_path, index=False)

    def _submit_id_mapping(self, from_db: str, to_db: str, ids: List[str]) -> str:
        """Submits a job to UniProt ID mapping API."""
        if not ids:
             raise ValueError("No IDs to map")

        data = urllib.parse.urlencode({
            "from": from_db,
            "to": to_db,
            "ids": ",".join(ids)
        }).encode("utf-8")

        req = urllib.request.Request(f"{UNIPROT_API_URL}/run", data=data)

        try:
            with urllib.request.urlopen(req) as f:
                response = json.load(f)
                return response["jobId"]
        except urllib.error.HTTPError as e:
            print(f"HTTP Error submitting job: {e.code} {e.reason}")
            print(e.read().decode())
            raise

    def _check_id_mapping_results(self, job_id: str) -> Tuple[bool, Dict]:
        """Checks status of a job."""
        # We need to handle the 303 redirect manually or detect it
        req = urllib.request.Request(f"{UNIPROT_API_URL}/status/{job_id}")
        try:
            with urllib.request.urlopen(req) as f:
                # If we were redirected to the results page, the URL will be different
                final_url = f.geturl()
                if "/results/" in final_url:
                    return True, {"jobStatus": "FINISHED"}

                response = json.load(f)
                status = response.get("jobStatus")

                if status == "FINISHED":
                    return True, response
                elif status in ("ERROR", "FAILED"):
                    raise Exception(f"UniProt Job failed: {response}")
                return False, response
        except urllib.error.HTTPError as e:
            # Sometimes explicit 303 handling is needed if client doesn't follow
            print(f"HTTP Error checking status: {e.code} {e.reason}")
            return False, {}

    def _get_id_mapping_results_stream(self, job_id: str) -> Dict:
        """Fetches results for a finished job."""
        url = f"{UNIPROT_API_URL}/uniprotkb/results/stream/{job_id}?format=json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as f:
             return json.load(f)

    def map_genes_to_uniprot(self, gene_symbols: List[str], organism_id: str = "9606") -> pd.DataFrame:
        """
        Maps gene symbols to UniProt Accessions using the async API.
        Filters by organism (Human=9606 by default).
        """
        # Filter out already cached
        to_fetch = [
            g for g in gene_symbols
            if g not in self.cache['gene_symbol'].values
        ]

        if not to_fetch:
            print("✨ All genes found in cache.")
            return self.cache[self.cache['gene_symbol'].isin(gene_symbols)]

        if self.dry_run:
            print(f"⚠️ Dry Run: Skipping network map for {len(to_fetch)} genes.")
            return self.cache

        print(f"📡 Submitting mapping job for {len(to_fetch)} genes to UniProt...")

        try:
            # Step 1: Submit
            job_id = self._submit_id_mapping("Gene_Name", "UniProtKB", to_fetch)
            print(f"   Job ID: {job_id}")

            # Step 2: Poll
            waiting = True
            retries = 0
            while waiting:
                 finished, status_resp = self._check_id_mapping_results(job_id)
                 if finished:
                     waiting = False
                 else:
                     status_str = status_resp.get('jobStatus', 'Unknown')
                     print(f"   ... waiting for UniProt (status: {status_str})")
                     time.sleep(POLLING_INTERVAL)
                     retries += 1
                     if retries > MAX_RETRIES:
                         raise TimeoutError("UniProt API timed out.")

            # Step 3: Fetch
            print("   Fetching results...")
            data = self._get_id_mapping_results_stream(job_id)

            # Step 4: Parse
            results = data.get("results", [])
            new_rows = []

            processed_genes = set()

            for item in results:
                input_gene = item.get("from")
                to_entry = item.get("to", {})

                # Check organism
                taxon = to_entry.get("organism", {}).get("taxonId", 0)
                if str(taxon) != str(organism_id):
                    continue

                accession = to_entry.get("primaryAccession")
                entry_type = to_entry.get("entryType", "UniProtKB unreviewed (TrEMBL)")
                is_reviewed = "Swiss-Prot" in entry_type

                existing = next((r for r in new_rows if r['gene_symbol'] == input_gene), None)

                if existing:
                    if is_reviewed and not existing['_is_reviewed']:
                        existing['uniprot_accession'] = accession
                        existing['_is_reviewed'] = True
                        existing['notes'] = "Promoted to Reviewed"
                else:
                    new_rows.append({
                        'gene_symbol': input_gene,
                        'uniprot_accession': accession,
                        'organism_id': str(taxon),
                        'status': 'mapped',
                        'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        '_is_reviewed': is_reviewed
                    })
                processed_genes.add(input_gene)

            # Mark missing
            for g in to_fetch:
                if g not in processed_genes:
                    new_rows.append({
                        'gene_symbol': g,
                        'uniprot_accession': None,
                        'organism_id': None,
                        'status': 'not_found',
                        'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    })

            for r in new_rows:
                if '_is_reviewed' in r: del r['_is_reviewed']

            new_df = pd.DataFrame(new_rows)
            self.cache = pd.concat([self.cache, new_df], ignore_index=True)
            self._save_cache()

        except Exception as e:
            print(f"❌ Error during UniProt mapping: {e}")
            if not self.cache.empty:
                 return self.cache
            raise e

        return self.cache[self.cache['gene_symbol'].isin(gene_symbols)]
