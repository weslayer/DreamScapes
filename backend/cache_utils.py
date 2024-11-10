from redis import Redis as Redis
from redis.exceptions import ConnectionError
from redisvl.query import VectorQuery
from redisvl.index import SearchIndex
from redisvl.utils.vectorize import OpenAITextVectorizer
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import numpy as np

load_dotenv()


class CacheServer:
    def __init__(self):
        self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "dreamscapeassetbucket")
        # self.REDIS_USER = os.getenv("REDIS_USER", "empty")
        # self.REDIS_PASS = os.getenv("REDIS_PASSWORD", "empty")
        # self.REDIS_HOST = os.getenv("REDIS_HOST", "empty")
        # self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        self.REDIS_URL = os.getenv("REDIS_URL", "localhost")

        # INSTANTIATE REDIS
        # redis_client = Redis(
        #     host=self.REDIS_HOST,
        #     port=self.REDIS_PORT,
        #     username=self.REDIS_USER,
        #     password=self.REDIS_PASS,
        #     db=0,
        # )

        redis_client = Redis.from_url(self.REDIS_URL)

        # Verify Redis connection
        try:
            redis_client.ping()
            print("Connected to Redis")
        except ConnectionError:
            print("Failed to connect to Redis")
            exit(1)

        # Define Redis schema
        schema = {
            "index": {
                "name": "user_object_index",
                "prefix": "user_voice_object_description:",
            },
            "fields": [
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "datatype": "float32",
                        "dims": 1536,
                        "distance_metric": "COSINE",  # or "L2" for Euclidean distance
                        "algorithm": "HNSW",
                    },
                },
                {
                    "name": "url",
                    "type": "text",
                },
            ],
        }

        # Create SearchIndex from schema
        index = SearchIndex.from_dict(schema)

        # Set Redis client for the index
        index.set_client(redis_client)

        # Connect and create the index
        index.connect(self.REDIS_URL)
        index.create(overwrite=True)

        self.index = index

        # INSTANTIATE BLOB STORAGE
        self.blob_storage = boto3.client("s3")

    def getEmbedding(self, objectName):
        api_key = os.environ.get("OPENAI_API_KEY")
        oai = OpenAITextVectorizer(
            model="text-embedding-ada-002",
            api_config={"api_key": api_key},
        )
        embedding = oai.embed(objectName)
        return embedding

    def get(self, embedding, objectName):
        output_dir = "output/"
        object_dir = os.path.join(output_dir, objectName)

        # Check if folder with the object name exists
        if os.path.isdir(object_dir):
            return f"{object_dir}/{objectName}.obj"

        # Search for matching objects
        v = VectorQuery(embedding, "embedding", return_fields=["url"])
        results = self.index.query(v)

        # return top result's url
        return results[0]["url"] if len(results) > 0 else False

    def post(self, obj_file_path, embedding):
        # Upload file to S3
        with open(obj_file_path, "rb") as f:
            try:
                self.blob_storage.upload_fileobj(f, self.S3_BUCKET_NAME, obj_file_path)

            except Exception as e:
                print(f"Error uploading file to S3: {e}")
                return None

        # Add mapping to vector db
        url = (
            f"https://dreamscapeassetbucket.s3.us-west-1.amazonaws.com/{obj_file_path}"
        )
        data = [
            {
                "user_object_index": np.array(embedding, dtype=np.float32).tobytes(),
                "url": obj_file_path,
            }
        ]
        self.index.load(data)

        return url

