from langpoem import Ollama
from langpoem.agents import AppinsightAgent


def run(text=''):
    return (
        AppinsightAgent()
            .llm(Ollama())
            .text(text)
            .build()
    ).run()
