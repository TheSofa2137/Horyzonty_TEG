import pytest
from unittest.mock import MagicMock, patch
import tools  # We import tools to patch its internal driver

# --- 1. Test: city_exists_in_graph ---
def test_city_exists_in_graph_found():
    """Verifies the function returns True when Neo4j finds a match."""
    # We create a mock for the session and the result
    mock_session = MagicMock()
    mock_result = MagicMock()
    
    # Simulate Neo4j returning a record with count: 1
    mock_result.single.return_value = {"count": 1}
    mock_session.run.return_value = mock_result
    
    # Patch the driver in tools.py so it uses our mock_session
    with patch("tools.driver.session") as mocked_session_context:
        mocked_session_context.return_value.__enter__.return_value = mock_session
        
        assert tools.city_exists_in_graph("Lisbon") is True
        # Verify the correct Cypher was called
        args, kwargs = mock_session.run.call_args
        assert "MATCH (c:City {name: $city})" in args[0]
        assert kwargs["city"] == "Lisbon"

def test_city_exists_in_graph_not_found():
    """Verifies the function returns False when Neo4j finds nothing."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    
    mock_result.single.return_value = {"count": 0}
    mock_session.run.return_value = mock_result
    
    with patch("tools.driver.session") as mocked_session_context:
        mocked_session_context.return_value.__enter__.return_value = mock_session
        assert tools.city_exists_in_graph("Atlantis") is False

# --- 2. Test: search_flights ---
def test_search_flights_filtering():
    """Checks if flight results are correctly parsed and filtered by budget."""
    mock_session = MagicMock()
    
    # Mock data exactly as Neo4j would return it
    mock_record_1 = {"airline": "Ryanair", "price": 200.0}
    mock_record_2 = {"airline": "LOT", "price": 500.0}
    
    # Simulate the session returning an iterator of these records
    mock_session.run.return_value = [mock_record_1, mock_record_2]
    
    with patch("tools.driver.session") as mocked_session_context:
        mocked_session_context.return_value.__enter__.return_value = mock_session
        
        # Call search with a budget of 300
        results = tools.search_flights("Rome", budget=300.0)
        
        # It should only return the flight that costs 200
        assert len(results) == 1
        assert results[0]["airline"] == "Ryanair"
        assert results[0]["price"] == 200.0

# --- 3. Test: search_hotels ---
def test_search_hotels_structure():
    """Verifies hotel search returns the expected dictionary structure."""
    mock_session = MagicMock()
    mock_session.run.return_value = [{"name": "Grand Hotel", "price": 150.0}]
    
    with patch("tools.driver.session") as mocked_session_context:
        mocked_session_context.return_value.__enter__.return_value = mock_session
        
        results = tools.search_hotels("Paris", budget=1000.0)
        
        assert len(results) == 1
        assert "name" in results[0]
        assert "price" in results[0]
        assert results[0]["name"] == "Grand Hotel"

# --- 4. Test: city_has_neighbourhoods ---
def test_city_has_neighbourhoods_logic():
    """Tests if the check for existing neighbourhood nodes works."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    
    # Mocking that 5 neighbourhoods exist for this city
    mock_result.single.return_value = {"count": 5}
    mock_session.run.return_value = mock_result
    
    with patch("tools.driver.session") as mocked_session_context:
        mocked_session_context.return_value.__enter__.return_value = mock_session
        assert tools.city_has_neighbourhoods("Barcelona") is True