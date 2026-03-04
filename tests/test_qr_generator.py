import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import app.qr_generator as qr


def test_is_valid_url_true():
    with patch("validators.url", return_value=True):
        assert qr.is_valid_url("https://example.com") is True


def test_is_valid_url_false(caplog):
    with patch("validators.url", return_value=False):
        with caplog.at_level(logging.ERROR):
            assert qr.is_valid_url("bad-url") is False
            assert "Invalid URL provided" in caplog.text


def test_create_directory_success(tmp_path):
    new_dir = tmp_path / "newdir"
    qr.create_directory(new_dir)
    assert new_dir.exists()


def test_create_directory_failure():
    with patch.object(Path, "mkdir", side_effect=Exception("fail")), \
         patch("builtins.exit") as mock_exit:
        qr.create_directory(Path("fake"))
        mock_exit.assert_called_once_with(1)


def test_generate_qr_code_invalid_url(tmp_path):
    with patch("app.qr_generator.is_valid_url", return_value=False):
        qr.generate_qr_code(
            "bad-url",
            tmp_path / "file.png"
        )


def test_generate_qr_code_success(tmp_path):
    fake_img = MagicMock()
    fake_qr = MagicMock()
    fake_qr.make_image.return_value = fake_img

    with patch("app.qr_generator.is_valid_url", return_value=True), \
         patch("qrcode.QRCode", return_value=fake_qr):

        output_file = tmp_path / "qr.png"
        qr.generate_qr_code("https://example.com", output_file)

        fake_qr.add_data.assert_called_once()
        fake_img.save.assert_called_once()


def test_generate_qr_code_exception(tmp_path, caplog):
    with patch("app.qr_generator.is_valid_url", return_value=True), \
         patch("qrcode.QRCode", side_effect=Exception("boom")):
        with caplog.at_level(logging.ERROR):
            qr.generate_qr_code("https://example.com", tmp_path / "qr.png")
            assert "An error occurred" in caplog.text


def test_main(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["prog", "--url", "https://example.com"])
    monkeypatch.setenv("QR_CODE_DIR", str(tmp_path))

    with patch("app.qr_generator.generate_qr_code") as mock_generate:
        qr.main()
        assert mock_generate.called
