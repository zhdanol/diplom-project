from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class BurstRateThrottle(UserRateThrottle):
    
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    
    scope = 'sustained'
    
class RegistrationThrottle(AnonRateThrottle):
    
    scope = 'registration'

class LoginThrottle(AnonRateThrottle):
    
    scope = 'login'

class PartnerThrottle(UserRateThrottle):
    
    scope = 'partner'
    
class ProductUpdateTrhottle(UserRateThrottle):
    
    scope = 'product_update'

class SocialAuthThrottle(AnonRateThrottle):
    
    scope = 'social-auth'