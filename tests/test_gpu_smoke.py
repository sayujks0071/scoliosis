import pytest

pytestmark = pytest.mark.gpu


def test_cuda_available():
    import torch

    assert torch.cuda.is_available()


def test_gpu_matmul_finite():
    import torch

    x = torch.randn(128, 128, device="cuda")
    y = (x @ x.T).sum()
    assert torch.isfinite(y).item()


def test_gpu_capability_ampere_or_newer():
    import torch

    major, minor = torch.cuda.get_device_capability(0)
    assert major >= 8, (
        f"expected Ampere (sm_8x) or newer; got sm_{major}{minor} "
        f"on {torch.cuda.get_device_name(0)}"
    )
