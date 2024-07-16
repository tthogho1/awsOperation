import torch
import boto3
import json
import os
import io

from PIL import Image
from pymongo import MongoClient
from transformers import AutoProcessor,CLIPProcessor, CLIPModel, CLIPTokenizer

# AWS設定
session = boto3.Session(profile_name='myregion',region_name='ap-northeast-1')

#sqs = boto3.client('sqs')
sqs = session.client('sqs')
s3_client = session.client('s3')
queue_url = '<sqs_url>'


def get_model_info(model_ID, device):
	model = CLIPModel.from_pretrained(model_ID).to(device)
	processor = AutoProcessor.from_pretrained(model_ID)
	tokenizer = CLIPTokenizer.from_pretrained(model_ID)
    # Return model, processor & tokenizer
	return model, processor, tokenizer

# Set the device
device = "cuda" if torch.cuda.is_available() else "cpu"
model_ID = "openai/clip-vit-base-patch32"

model, processor, tokenizer = get_model_info(model_ID, device)

def get_single_image_embedding(my_image):
    image = processor(images=my_image , return_tensors="pt")
    embedding = model.get_image_features(**image).float()
    # convert the embeddings to numpy array
    return embedding.cpu().detach().numpy()

driver_URL = '<mongodb_url>'
vector_database_field_name= 'embed'
def process_message(message):
    body = json.loads(message['Body'])
    
    Records = body['Records']
    s3 = Records[0]['s3']
    
    bucket = s3['bucket']['name']
    key = s3['object']['key']
    
    file_content = io.BytesIO()
    # key is filename (id.jpg)
    s3_client.download_fileobj(bucket, key, file_content)
    
    file_content.seek(0)
    image = Image.open(file_content)
    
    imageFeature_np = get_single_image_embedding(image)
    imageEmbedding = imageFeature_np[0].tolist()

    with MongoClient(driver_URL) as client :
        webcamDb = client.webcam
        webCamCol = webcamDb.webcam

        id = key.split(".")[0]
        webCamInfo = webCamCol.find_one({'webcamid': int(id)})        
        if vector_database_field_name not in webCamInfo:
            webCamInfo[vector_database_field_name] = imageEmbedding            
            webCamCol.replace_one({'_id': webCamInfo['_id']}, webCamInfo)

    #collection.insert_one(document)
    print(imageEmbedding)
    
def main():
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )
        
        if 'Messages' in response:
            for message in response['Messages']:
                try:
                    process_message(message)
                    
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                except Exception as e:
                    print(f"error occured: {str(e)}")

if __name__ == "__main__":
    main()