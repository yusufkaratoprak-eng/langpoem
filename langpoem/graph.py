class RuntimeGraph:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self):
        print(f"Running graph: {self.cfg['name']}")
        print("LLM:", self.cfg["llm"])
        print("Memory:", self.cfg["memory"])
        print("Agents:")
        for a in self.cfg["agents"]:
            print(" -", a["name"], "=>", a["prompt"])
        print("Flow:", self.cfg["flow"])


class AgentBuilder:
    def __init__(self, graph, name):
        self.graph = graph
        self.agent = {"name": name, "prompt": ""}

    def prompt(self, text):
        print(f"[Agent] prompt -> {text}")
        self.agent["prompt"] = text
        self.graph._agents.append(self.agent)
        return self.graph


class Graph:
    def __init__(self, name):
        self.name = name
        self._llm = None
        self._memory = None
        self._agents = []
        self._flow = ""

    def llm(self, llm):
        print("[Graph] LLM configured")
        self._llm = llm
        return self

    def memory(self, mem):
        print("[Graph] Memory configured")
        self._memory = mem
        return self

    def agent(self, name):
        print(f"[Graph] Creating agent: {name}")
        return AgentBuilder(self, name)

    def flow(self, expr):
        print(f"[Graph] Flow: {expr}")
        self._flow = expr
        return self

    def build(self):
        print("[Graph] Build complete")
        return RuntimeGraph({
            "name": self.name,
            "llm": self._llm,
            "memory": self._memory,
            "agents": self._agents,
            "flow": self._flow
        })
