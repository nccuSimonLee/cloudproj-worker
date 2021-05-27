class Judger:
    def __init__(self, rekog):
        self.rekog = rekog

    def judge_if_focus(self, bucket_name, key):
        response = self.rekog.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': key,
                }
            }
        )
        has_face = self._check_has_face(response)
        return has_face

    def _check_has_face(self, response):
        return bool(response['FaceDetails'])