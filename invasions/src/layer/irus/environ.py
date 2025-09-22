import os
import boto3
from aws_lambda_powertools import Logger

class IrusResources:

    _logger = None
    _session = None
    _s3 = None
    _s3_resource = None
    _bucket_name : str = None
    _dynamodb = None
    _table_name : str = None
    _table = None
    _state_machine = None
    _process_step_function_arn : str = None
    _post_step_function_arn : str = None
    _textract = None
    _webhook_url : str = None
    _image_contrast_factor : float = None
    _image_saturation_factor : float = None


    @classmethod
    def logger(cls):
        if cls._logger == None:
            cls._logger = Logger()
        return cls._logger
    
    @classmethod
    def session(cls, profile:str = None):
        if cls._session == None:
            cls._session = boto3.session.Session(profile_name = profile)
        return cls._session

    @classmethod
    def s3(cls):
        if cls._s3 == None:
            cls._s3 = cls.session().client('s3')
        return cls._s3
    
    @classmethod
    def s3_resource(cls):
        if cls._s3_resource == None:
            cls._s3_resource = cls.session().resource('s3')
        return cls._s3_resource
    
    @classmethod
    def bucket_name(cls) -> str:
        if cls._bucket_name == None:
            cls._bucket_name = os.environ.get('BUCKET_NAME')
            if cls._bucket_name == None:
                raise ValueError('BUCKET_NAME environment variable is not set')
        return cls._bucket_name
    
    @classmethod
    def dynamodb(cls):
        if cls._dynamodb == None:
            cls._dynamodb = cls.session().resource('dynamodb')
        return cls._dynamodb
    
    @classmethod
    def table_name(cls) -> str:
        if cls._table_name == None:
            cls._table_name = os.environ.get('TABLE_NAME')
            if cls._table_name == None:
                raise ValueError('TABLE_NAME environment variable is not set')
        return cls._table_name
    
    @classmethod
    def table(cls):
        if cls._table == None:
            cls._table = cls.dynamodb().Table(cls.table_name())
        return cls._table
    
    @classmethod
    def state_machine(cls):
        if cls._state_machine == None:
            cls._state_machine = cls.session().client('stepfunctions')
        return cls._state_machine
    
    @classmethod
    def process_step_function_arn(cls) -> str:
        if cls._process_step_function_arn == None:
            cls._process_step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
            if cls._process_step_function_arn == None:
                raise ValueError('PROCESS_STEP_FUNC environment variable is not set')
        return cls._process_step_function_arn

    @classmethod
    def post_step_function_arn(cls) -> str:
        if cls._post_step_function_arn == None:
            cls._post_step_function_arn = os.environ.get('POST_STEP_FUNC')
            if cls._post_step_function_arn == None:
                raise ValueError('POST_STEP_FUNC environment variable is not set')
        return cls._post_step_function_arn

    @classmethod
    def textract(cls):
        if cls._textract == None:
            cls._textract = cls.session().client('textract')
        return cls._textract
    
    @classmethod
    def webhook_url(cls) -> str:
        if cls._webhook_url == None:
            cls._webhook_url = os.environ.get('WEBHOOK_URL')
            if cls._webhook_url == None:
                raise ValueError('WEBHOOK_URL environment variable is not set')
        return cls._webhook_url
    
    @classmethod
    def image_contrast_factor(cls) -> float:
        if cls._image_contrast_factor == None:
            cls._image_contrast_factor = float(os.environ.get('IMAGE_CONTRAST_FACTOR', '1.5'))
        return cls._image_contrast_factor
    
    @classmethod
    def image_saturation_factor(cls) -> float:
        if cls._image_saturation_factor == None:
            cls._image_saturation_factor = float(os.environ.get('IMAGE_SATURATION_FACTOR', '0.7'))
        return cls._image_saturation_factor



class IrusSecrets:

    _ssm = None
    _public_key_path : str = None
    _public_key : str = None
    _public_key_bytes : bytes = None
    _app_id_path : str = None
    _app_id : str = None
    _role_id_path : str = None
    _role_id : str = None

    @classmethod
    def ssm(cls):
        if cls._ssm == None:
            cls._ssm = boto3.client('ssm')
        return cls._ssm

    @classmethod
    def public_key_path(cls) -> str:
        if cls._public_key_path == None:
            cls._public_key_path = os.environ['PUBLIC_KEY_PATH']
        return cls._public_key_path
    
    @classmethod
    def public_key(cls):
        if cls._public_key == None:
            cls._public_key = cls.ssm().get_parameter(Name=cls.public_key_path(), WithDecryption=True)['Parameter']['Value']
        return cls._public_key
    
    @classmethod
    def public_key_bytes(cls) -> bytes:
        if cls._public_key_bytes == None:
            cls._public_key_bytes = bytes.fromhex(cls.public_key())
        return cls._public_key_bytes
    
    @classmethod
    def app_id_path(cls) -> str:
        if cls._app_id_path == None:
            cls._app_id_path = os.environ['APP_ID_PATH']
        return cls._app_id_path
    
    @classmethod
    def app_id(cls) -> str:
        if cls._app_id == None:
            cls._app_id = cls.ssm().get_parameter(Name=cls.app_id_path(), WithDecryption=True)['Parameter']['Value']
        return cls._app_id

    @classmethod
    def role_id_path(cls) -> str:
        if cls._role_id_path == None:
            cls._role_id_path = os.environ['ROLE_ID_PATH']
        return cls._role_id_path
    
    @classmethod
    def role_id(cls) -> str:
        if cls._role_id == None:
            cls._role_id = cls.ssm().get_parameter(Name=cls.role_id_path(), WithDecryption=True)['Parameter']['Value']
        return cls._role_id

