import asyncio
import os
import sys

from playwright.async_api import async_playwright

MMD_FILE = "docs/figures/scoliosis_mechanism_map.mmd"
HTML_FILE = "temp_mermaid.html"
PNG_FILE = "docs/figures/scoliosis_mechanism_map.png"
SVG_FILE = "docs/figures/scoliosis_mechanism_map.svg"

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true });
    </script>
    <style>
        body { background-color: white; }
    </style>
</head>
<body>
    <pre class="mermaid">
%s
    </pre>
</body>
</html>
"""

async def main():
    if not os.path.exists(MMD_FILE):
        print(f"Error: {MMD_FILE} not found.")
        sys.exit(1)

    with open(MMD_FILE, 'r') as f:
        mmd_content = f.read()

    # Escape backticks if any (though unlikely in mermaid graph usually)
    # Using simple string replacement for the template
    html_content = TEMPLATE % mmd_content

    with open(HTML_FILE, 'w') as f:
        f.write(html_content)

    print(f"Rendering {MMD_FILE}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(HTML_FILE)}")

        # Wait for mermaid to render
        try:
            await page.wait_for_selector(".mermaid > svg", timeout=10000)
        except Exception as e:
            print(f"Error rendering mermaid: {e}")
            await browser.close()
            sys.exit(1)

        # Get the SVG element locator
        svg_locator = page.locator(".mermaid > svg").first

        # Screenshot to PNG
        # Set viewport to content size or large enough
        bbox = await svg_locator.bounding_box()
        if bbox:
            await page.set_viewport_size({"width": int(bbox['width']) + 50, "height": int(bbox['height']) + 50})

        await svg_locator.screenshot(path=PNG_FILE)
        print(f"Saved PNG to {PNG_FILE}")

        # Get SVG content and save
        svg_outer_html = await page.evaluate("document.querySelector('.mermaid > svg').outerHTML")

        with open(SVG_FILE, 'w') as f:
            f.write(svg_outer_html)
        print(f"Saved SVG to {SVG_FILE}")

        await browser.close()

    if os.path.exists(HTML_FILE):
        os.remove(HTML_FILE)

if __name__ == "__main__":
    asyncio.run(main())
