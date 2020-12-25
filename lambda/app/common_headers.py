import os
def create_common_header():
    return {
                'Access-Control-Allow-Origin': os.environ['AllowOrigin'][1:-1],
                'Access-Control-Allow-Headers': 'Origin, Authorization, Accept, Content-Type',
                'Access-Control-Allow-Credentials': 'true'
            }