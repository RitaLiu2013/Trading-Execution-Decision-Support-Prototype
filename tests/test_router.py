from trading_ai.router import route_question


def test_router_examples():
    assert route_question("What is implementation shortfall?")["route"] == "knowledge"
    assert route_question("Which venue has the worst average execution slippage?")["route"] == "data"
    assert route_question("Show the top 5 worst executions")["tool"] == "worst_executions"
    assert route_question("How do I make pizza?")["route"] == "unsupported"
    assert route_question("What problem does MCP solve?")["route"] == "unsupported"
