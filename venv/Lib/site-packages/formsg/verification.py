import base64
import logging

from nacl.signing import VerifyKey

from formsg.schemas.verification import VerificationAuthenticateOptions
from formsg.util.parser import parse_verification_signature
from formsg.util.verification import format_to_base_string, is_signature_time_valid

logger = logging.getLogger(__name__)


class Verification(object):
    def __init__(
        self,
        verification_public_key: str,
        verification_secret_key: str,
        transaction_expiry: int,
    ):
        self.verification_public_key = verification_public_key
        self.verification_secret_key = verification_secret_key
        self.transaction_expiry = transaction_expiry

    """
      /**
   *  Verifies signature
   * @param {object} data
   * @param {string} data.signatureString
   * @param {number} data.submissionCreatedAt date in milliseconds
   * @param {string} data.fieldId
   * @param {string} data.answer
   * @param {string} data.publicKey
   */
    """

    def authenticate(
        self, verification_authenticate_options: VerificationAuthenticateOptions
    ):
        # FIXME: runtime checks at top level
        [signature_string, submission_created_at, field_id, answer] = [
            verification_authenticate_options["signatureString"],
            verification_authenticate_options["submissionCreatedAt"],
            verification_authenticate_options["fieldId"],
            verification_authenticate_options["answer"],
        ]
        try:
            verification_signature = parse_verification_signature(signature_string)
            [transaction_id, time_, form_id, signature] = [
                verification_signature["v"],
                verification_signature["t"],
                verification_signature["f"],
                verification_signature["s"],
            ]
            if not time_:
                raise Exception("Malformed signature string was passed into function")
            if is_signature_time_valid(
                time_, submission_created_at, self.transaction_expiry
            ):
                format_to_base_string_params = {
                    "transactionId": transaction_id,
                    "formId": form_id,
                    "fieldId": field_id,
                    "answer": answer,
                    "time": time_,
                }
                data = format_to_base_string(format_to_base_string_params)
                """
                return nacl.sign.detached.verify(
                    decodeUTF8(data),
                    decodeBase64(signature),
                    decodeBase64(this.verificationPublicKey)
                )
                """
                verify_key = VerifyKey(base64.b64decode(self.verification_public_key))
                return verify_key.verify(
                    smessage=data.encode("utf-8"),
                    signature=base64.b64decode(signature),
                )

            else:
                logger.info(
                    f'Signature was expired for signatureString="{signature_string}" signatureDate="{time_}" submissionCreatedAt="{submission_created_at}'
                )
                return False
        except Exception as e:
            print(e)
            return False
