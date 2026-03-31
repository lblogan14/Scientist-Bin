# Scientist-Bin Backend

This is the backend of Scientist-Bin, which is responsible for managing the multi-agent system and orchestrating the training and deployment of data science models. It provides APIs for the frontend to interact with the agents and handles the communication between them.

The backend is built using Python, LangGraph, and FastAPI. It uses a modular architecture to allow for easy integration of new agents and frameworks. The backend also includes a database for storing model information, training results, and deployment status.

# Codebase best practices
- Follow a modular architecture to allow for easy integration of new agents and frameworks.
- Use clear and consistent naming conventions for files, classes, functions, and variables.
- Write comprehensive documentation for each module, class, and function to explain their purpose and usage.
- Implement error handling and logging to facilitate debugging and maintenance (Pytest for testing and logging module for logging).
- Use `uv` for managing dependencies and virtual environments to ensure consistency across different development environments.
- Use ruff and lint for code formatting and linting to maintain code quality and readability.

## Proposed Codebase Structure

Comply with the `src` and `tests` structure. Inside `src`, we will have - the main application code, 
- the `agents` directory for the different agents,
- the `models` directory for the data science models,
- the `data` directory for any datasets,
- the `preprocessing` directory for data preprocessing scripts,
- the `training` directory for training scripts,
- the `evaluation` directory for evaluation scripts,
- the `postprocessing` directory for post-processing scripts,
- the `api` directory for the FastAPI endpoints,
- the `utils` directory for utility functions.

Inside `agents`, we will have subdirectories for each subagent to handle different frameworks (PyTorch, TensorFlow, Scikit-learn, Hugging Face Transformers, Hugging Face Diffusers). Each subagent will have its own implementation for training and deploying models specific to its framework. There will be a common interface for all agents to ensure consistency in how they are called and how they interact with the rest of the system. There will also be a central agent that coordinates the activities of the subagents and manages the overall workflow of training and deployment.

For each subagent and the central agent, we will have separate files to manage their specific functionalities for agentic structure (following what langgraph needs):
- `graph.py` for defining the agent's graph structure and interactions,
- `agent.py` for implementing the agent's logic and behavior,
- `states.py` for defining the states and transitions of the agent,
- `schemas.py` for defining the data schemas used by the agent (structured outputs, inputs, etc.),
- `utils.py` for any utility functions specific to the agent.
- `nodes/` directory for defining the nodes used in the agent's graph, with separate files for different types of nodes (e.g., data processing nodes, model training nodes, evaluation nodes, deployment nodes, etc.).
- `prompts/` directory for defining the prompts used by the agent, with separate files for different types of prompts (e.g., data processing prompts, model training prompts, evaluation prompts, deployment prompts, etc.).
- `skills/` directory for defining the skills used by the agent, with separate files for different types of skills (e.g., data processing skills, model training skills, evaluation skills) (Mimicking the official implementation and format of Agent skills defined by Anthropic's agentic structure). We need to implement the function to read the skills from the `skills/` directory and integrate them into the agent's graph structure. This will allow us to easily add new skills for different frameworks and functionalities without having to modify the core logic of the agent. Each skill will be defined in its own file, with a clear interface for how it can be called and what inputs and outputs it expects. The central agent will then be able to call these skills as needed during the training and deployment process, allowing for a flexible and modular approach to managing the different tasks involved in training and deploying data science models.


# To start with
Focus on 
- building a central agent that can coordinate the activities of the subagents and manage the overall workflow of training and evaluation. Building 
- building a subagent for scikit-learn framework, which will handle the training and evaluation of models using scikit-learn. This will involve implementing the necessary logic for data preprocessing, model training, and evaluation specific to scikit-learn, as well as defining the appropriate graph structure and interactions for the subagent. We can then use this subagent as a template for building additional subagents for other frameworks like PyTorch, TensorFlow, Hugging Face Transformers, and Hugging Face Diffusers.