import unittest
from unittest.mock import patch, MagicMock, mock_open
import virtuallab_client as client


class TestVirtualLabClient(unittest.TestCase):
    URL = "http://localhost:80"

    @patch("virtuallab_client.requests.post")
    def test_register_user_envia_datos_correctos(self, mock_post):
        mock_response = MagicMock()
        mock_response.content = b"User Ana with role student registered"
        mock_post.return_value = mock_response

        res = client.registerUser(self.URL, "Ana", 55, "student", "pass123")

        mock_post.assert_called_once_with(
            "http://localhost:80/register",
            data="name=Ana&id=55&role=student&password=pass123"
        )
        self.assertEqual(res, "User Ana with role student registered")

    @patch("virtuallab_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"contenido_zip")
    def test_upload_lab_envia_headers_y_binario(self, mock_file, mock_post):
        mock_response = MagicMock()
        mock_response.content = b"File was succesfully received"
        mock_post.return_value = mock_response

        res = client.uploadLab(self.URL, 787878, "ruta/falsa/rc.zip")

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:80/upload_lab")
        self.assertEqual(kwargs["headers"], {"X-File-Name": "rc.zip", "X-Client-ID": "787878"})
        self.assertEqual(res, "File was succesfully received")
