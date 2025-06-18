from unittest.mock import patch
from genlayer_py.client.client import GenLayerClient, create_client
from genlayer_py.chains import localnet


def test_create_client_default():
    """Test creating a client with default parameters"""
    with patch.object(
        GenLayerClient, "initialize_consensus_smart_contract"
    ) as mock_init:
        client = create_client()
        assert isinstance(client, GenLayerClient)
        assert client.provider is not None
        mock_init.assert_called_once()


def test_create_client_localnet():
    """Test creating a client with localnet chain"""
    with patch.object(
        GenLayerClient, "initialize_consensus_smart_contract"
    ) as mock_init:
        client = create_client(chain=localnet)
        assert isinstance(client, GenLayerClient)
        assert client.chain == localnet
        assert client.provider is not None
        mock_init.assert_called_once()


def test_create_client_with_endpoint():
    """Test creating a client with a custom endpoint"""
    with patch.object(
        GenLayerClient, "initialize_consensus_smart_contract"
    ) as mock_init:
        custom_endpoint = "http://custom-endpoint:8545"
        client = create_client(chain=localnet, endpoint=custom_endpoint)
        assert isinstance(client, GenLayerClient)
        assert client.provider is not None
        assert client.chain.rpc_urls["default"]["http"] == [custom_endpoint]
        mock_init.assert_called_once()
