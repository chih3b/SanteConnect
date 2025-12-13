"""
MLX-LM integration for faster inference on Apple Silicon
With proper tool calling support for LangGraph
"""

from typing import Any, List, Optional, Dict
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.messages import AIMessage
import json
import re


class MLXLLM(LLM):
    """
    Custom LangChain LLM wrapper for MLX-LM
    Optimized for Apple Silicon with tool calling support
    """
    
    model_name: str = "mlx-community/Qwen2.5-3B-Instruct-4bit"
    max_tokens: int = 512
    temperature: float = 0.1
    
    _model: Any = None
    _tokenizer: Any = None
    _tools: List[Any] = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_model()
    
    def _load_model(self):
        """Load MLX model"""
        if self._model is None:
            from mlx_lm import load
            print(f"🚀 Loading MLX model: {self.model_name}...")
            self._model, self._tokenizer = load(self.model_name)
            print("✅ MLX model loaded")
    
    @property
    def _llm_type(self) -> str:
        return "mlx"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call MLX model"""
        from mlx_lm import generate
        
        # Generate response
        response = generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            verbose=False
        )
        
        return response
    
    def bind_tools(self, tools: List[Any]) -> "MLXLLM":
        """Bind tools to the model"""
        self._tools = tools
        return self
    
    def invoke(self, messages: List[Any]) -> Any:
        """
        Invoke the model with messages and tool calling support
        """
        # Convert messages to prompt with tool instructions
        prompt = self._messages_to_prompt_with_tools(messages)
        
        # Generate response
        response_text = self._call(prompt)
        
        # Parse for tool calls
        tool_calls = self._parse_tool_calls(response_text)
        
        # Debug: print what we found
        if tool_calls:
            print(f"✅ MLX parsed {len(tool_calls)} tool call(s)")
            for tc in tool_calls:
                print(f"   - {tc['name']}")
        
        # If tool calls found, return them in LangGraph format
        if tool_calls:
            # Remove JSON from content
            clean_content = re.sub(r'\{[^{}]*"tool_calls"[^{}]*\[[^\]]*\][^{}]*\}', '', response_text).strip()
            
            return AIMessage(
                content=clean_content if clean_content else "",
                tool_calls=tool_calls
            )
        
        # Otherwise return the text response
        return AIMessage(
            content=response_text,
            tool_calls=[]
        )
    
    def _messages_to_prompt_with_tools(self, messages: List[Any]) -> str:
        """Convert messages to prompt with tool calling instructions"""
        
        # Build tool descriptions
        tools_json = []
        if self._tools:
            for tool in self._tools:
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description
                    }
                    # Try to get args schema
                    if hasattr(tool, 'args_schema'):
                        try:
                            schema = tool.args_schema.schema()
                            tool_info["parameters"] = schema.get("properties", {})
                        except:
                            pass
                    tools_json.append(tool_info)
        
        # Build prompt
        prompt_parts = []
        
        # Add tool calling instructions
        if tools_json:
            tool_instruction = """You are a helpful assistant with access to tools. When you need to use a tool, respond ONLY with a JSON object in this exact format:

{"tool_calls": [{"name": "tool_name", "arguments": {"arg1": "value1", "arg2": "value2"}}]}

Available tools:
"""
            for tool in tools_json:
                tool_instruction += f"\n- {tool['name']}: {tool['description']}"
                if 'parameters' in tool:
                    tool_instruction += f"\n  Parameters: {', '.join(tool['parameters'].keys())}"
            
            tool_instruction += "\n\nIMPORTANT: You MUST use tools to answer questions. Do not answer directly without calling a tool first."
            prompt_parts.append(tool_instruction)
        
        # Add conversation messages
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                content = msg.content
                if hasattr(msg, 'type'):
                    if msg.type == 'human':
                        prompt_parts.append(f"\nUser: {content}")
                    elif msg.type == 'system':
                        prompt_parts.append(f"\nSystem: {content}")
                    elif msg.type == 'ai':
                        prompt_parts.append(f"\nAssistant: {content}")
                    elif msg.type == 'tool':
                        # Tool result
                        prompt_parts.append(f"\nTool Result: {content}")
        
        prompt = "\n".join(prompt_parts) + "\n\nAssistant:"
        return prompt
    
    def _parse_tool_calls(self, response: str) -> List[Dict]:
        """
        Parse tool calls from JSON response
        Returns format compatible with LangGraph
        Only takes the FIRST valid tool call to avoid confusion
        """
        tool_calls = []
        
        # Try to parse JSON response - look for FIRST valid JSON object
        try:
            # Find first JSON object with tool_calls
            json_pattern = r'\{[^{}]*"tool_calls"[^{}]*\[[^\]]*\][^{}]*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                try:
                    data = json.loads(json_str)
                    
                    if "tool_calls" in data and isinstance(data["tool_calls"], list):
                        # Only take the FIRST tool call
                        for tc in data["tool_calls"][:1]:  # Limit to first tool call
                            tool_name = tc.get("name", "")
                            
                            # Validate tool name (must end with _tool)
                            if tool_name and "_tool" in tool_name:
                                tool_calls.append({
                                    "name": tool_name,
                                    "args": tc.get("arguments", {}),
                                    "id": "call_0",
                                    "type": "tool_call"
                                })
                                break  # Only one tool call at a time
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"⚠️  Failed to parse tool calls: {e}")
        
        return tool_calls


def get_mlx_llm(model_name: str = "mlx-community/Qwen2.5-3B-Instruct-4bit") -> MLXLLM:
    """Get MLX LLM instance"""
    return MLXLLM(model_name=model_name)
