from flask import request

def userCheck():
    browser = request.user_agent.browser
    chrome_version = request.user_agent.version[:2]
    platform = request.user_agent.platform

    if browser and chrome_version and platform:
        if (platform == 'android' or platform == 'iphone'):
            raise ValueError('Unsupported devise')
        if (browser != 'chrome'):
            raise ValueError('Unsupported browser')
        if (chrome_version not in ['80', '81', '83']):
            raise ValueError('Unsupported Chrome version')
    
    return chrome_version