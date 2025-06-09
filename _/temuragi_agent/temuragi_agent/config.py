from wl_config_manager import ConfigManager
import pkg_resources


def load_config(path=None):
    # Determine config file location
    if path:
        config_path = path
    else:
        # default config.yaml bundled with package
        config_path = pkg_resources.resource_filename(__name__, 'config.yaml')

    # Default values matching config.yaml structure
    defaults = {
        'temuragi_agent.log_level': 5,
        'temuragi_agent.modules': 'build/',
        'temuragi_agent.ai_manager.tts': 'openai',
        'temuragi_agent.ai_manager.image': 'openai',
        'temuragi_agent.ai_manager.prompt_folder': None,
        'temuragi_agent.ai_manager.output_dir': None,
        'temuragi_agent.ai_manager.openai.api_key': None,
        'temuragi_agent.ai_manager.openai.organization_id': None,
        'temuragi_agent.ai_manager.openai.whisper_model': 'whisper-1',
        'temuragi_agent.ai_manager.openai.chat_model': 'gpt-4-turbo',
        'temuragi_agent.ai_manager.openai.tts_voice': 'alloy',
        'temuragi_agent.ai_manager.openai.tts_model': 'tts-1',
    }

    return ConfigManager(
        config_path=config_path,
        default_config=defaults,
        env_prefix='TEMURAGI_',  # e.g. TEMURAGI_TEMURAGI_AGENT_LOG_LEVEL
        required_keys=[
            'temuragi_agent.ai_manager.openai.api_key',
            'temuragi_agent.ai_manager.openai.organization_id',
        ],
    )