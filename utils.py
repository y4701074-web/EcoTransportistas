from db import get_user_language
from config import MESSAGES

def get_message(key, user_id, **kwargs):
    lang = get_user_language(user_id)
    # Fallback a 'es' si el idioma no existe
    lang_messages = MESSAGES.get(lang, MESSAGES['es'])
    # Fallback a la key si el mensaje no existe en el idioma
    message = lang_messages.get(key, MESSAGES['es'].get(key, key))
    
    return message.format(**kwargs) if kwargs else message
  
