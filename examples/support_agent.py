from langpoem import Graph, Ollama, SQLiteMemory

def build_graph():
    graph = (
        Graph("SupportAgent")
            .llm(Ollama())
            .memory(SQLiteMemory())
            .agent("planner")
                .prompt("Plan the task")
            .agent("coder")
                .prompt("Write code")
            .agent("reviewer")
                .prompt("Review output")
            .flow("planner >> coder >> reviewer")
            .build()
    )
    return graph
