def is_signature_time_valid(
    signature_time: int, submission_created_at: int, transaction_expiry: int
) -> bool:
    """
    Checks if signature was made within the given expiry range before submission was created.

    :param signature_time: in ms
    :param submission_created_at: in ms
    :rtype: :class:`bool`
    """
    max_time = submission_created_at
    min_time = max_time - transaction_expiry * 1000
    return signature_time > min_time and signature_time < max_time


def format_to_base_string(params) -> str:
    """
    Formats given data into a string for signing
    """
    [transaction_id, form_id, field_id, answer, time_] = [
        params["transactionId"],
        params["formId"],
        params["fieldId"],
        params["answer"],
        params["time"],
    ]

    return f"{transaction_id}.{form_id}.{field_id}.{answer}.{time_}"
