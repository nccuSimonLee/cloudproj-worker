import requests
import time
from opencc import OpenCC
cc = OpenCC('s2t')



class Extractor:
    def __init__(self, transcribe):
        self.transcribe = transcribe

    def extract_question(self, bucket_name, key):
        job_name = self._start_transcription_job(bucket_name, key)
        results = self._request_transcribe_results(job_name)
        texts = ''.join(line['transcript'] for line in results['transcripts'])
        question = self._extract_question(texts)
        return question

    def _start_transcription_job(self, bucket_name, key):
        job_name = "job_name"
        job_uri = f's3://{bucket_name}/{key}'
        self.transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='wav',
            LanguageCode='zh-CN'
        )
        return job_name

    def _request_transcribe_results(self, job_name):
        while True:
            status = self.transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            time.sleep(5)
        response = requests.get(status['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        self.transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        return response.json()['results']
    
    def _extract_question(self, texts):
        texts = cc.convert(texts)
        return texts
