from rest_framework.authtoken.models import Token
from .models import User
from django.contrib.auth import login



def save_user_profile(backend, user, response, *args, **kwargs):
    if backend.name in ['google-oauth2', 'github']:
        try:
            if response.get('email'):
                user.email = response['email']
            
            if backend.name == 'google-oauth2':
                user.first_name = response.get('given_name', '')
                user.last_name = response.get('family_name', '')
            elif backend.name == 'github':
                name_parts = response.get('name', '').split()
                if len(name_parts) >= 2:
                    user.first_name = name_parts[0]
                    user.last_name = ' '.join(name_parts[1:])
                else:
                    user.first_name = response.get('name', '')
            
            user.type = 'buyer'
            user.is_active = True
            
            user.save()
            
            Token.objects.get_or_create(user=user)
                
        except Exception as ex:
            print(f'Error in pipeline: {str(ex)}')
    
    return {'user': user}
            
def save_social_data(strategy, details, response, user=None, *args, **kwargs):
    request = strategy.request
    
    if user:
        request.session['social_auth_data'] = {
            'user_id': user.id,
            'email': user.email,
            'provider': strategy.backend.name,
            'extra_data': response
        }
        
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        request.session['auth_token'] = token.key
        
        login(request, user)
    return kwargs