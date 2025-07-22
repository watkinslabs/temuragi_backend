class TokenManager {
    constructor() {
        this.storage_keys = {
            api_token: 'api_token',
            refresh_token: 'refresh_token',
            user_id: 'user_id',
            user_info: 'user_info'
        };
        window.app.register('token_manager', this);
    }
    
    get_tokens() {
        return {
            api_token: localStorage.getItem(this.storage_keys.api_token),
            refresh_token: localStorage.getItem(this.storage_keys.refresh_token),
            user_id: localStorage.getItem(this.storage_keys.user_id)
        };
    }
    
    set_tokens(api_token, refresh_token, user_id) {
        if (api_token) localStorage.setItem(this.storage_keys.api_token, api_token);
        if (refresh_token) localStorage.setItem(this.storage_keys.refresh_token, refresh_token);
        if (user_id) localStorage.setItem(this.storage_keys.user_id, user_id);
    }
    
    update_api_token(api_token) {
        localStorage.setItem(this.storage_keys.api_token, api_token);
    }
    
    set_user_info(user_info) {
        localStorage.setItem(this.storage_keys.user_info, JSON.stringify(user_info));
    }
    
    get_user_info() {
        const info = localStorage.getItem(this.storage_keys.user_info);
        return info ? JSON.parse(info) : null;
    }
    
    clear_tokens() {
        Object.values(this.storage_keys).forEach(key => {
            localStorage.removeItem(key);
        });
    }
    
    has_tokens() {
        const tokens = this.get_tokens();
        return !!(tokens.api_token && tokens.refresh_token && tokens.user_id);
    }
}
