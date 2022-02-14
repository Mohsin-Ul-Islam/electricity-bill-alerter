import requests
import bs4

from twilio.rest import Client
from google.cloud.secretmanager import SecretManagerServiceClient


def handler():
    main()


def main():

    batch_no = "01"
    division = "11562"
    reference_no = "0024708"

    url = "http://www.lesco.gov.pk/Customer_Reg/AccountStatus.aspx?strRU=U"
    params = {"nBatchNo": batch_no, "nSubDiv": division, "nRefNo": reference_no}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return print("Oops! error getting bill status.")

    soup = bs4.BeautifulSoup(response.text, "html.parser")

    due_date = soup.find("td", string="Due Date")
    issue_date = soup.find("td", string="Bill Issue Date")
    payable = soup.find("td", string="Amount Payable Within Due Date")
    paid = soup.find("td", string="Amount Paid")

    paid = float(paid.next_sibling.next_sibling.text)
    payable = float(payable.next_sibling.next_sibling.text)
    due_date = due_date.next_sibling.next_sibling.text
    issue_date = issue_date.next_sibling.next_sibling.text

    if paid < payable:

        message = f"""
        Electricity bill payment alert!
        Due Date: {due_date}
        Issue Date: {issue_date}
        Payable: {payable - paid}
        More Info: {url}
        """

        secrets = SecretManagerServiceClient()
        username = secrets.access_secret_version(
            request=dict(
                name=secrets.secret_version_path(
                    "aqua-gcloud", "twilio-account-sid", "latest"
                )
            )
        ).payload.data.decode("utf-8")
        password = secrets.access_secret_version(
            request=dict(
                name=secrets.secret_version_path(
                    "aqua-gcloud", "twilio-auth-token", "latest"
                )
            )
        ).payload.data.decode("utf-8")
        phone = secrets.access_secret_version(
            request=dict(
                name=secrets.secret_version_path(
                    "aqua-gcloud", "twilio-phone-number", "latest"
                )
            )
        ).payload.data.decode("utf-8")
        personal = secrets.access_secret_version(
            request=dict(
                name=secrets.secret_version_path(
                    "aqua-gcloud", "aqua-phone-number", "latest"
                )
            )
        ).payload.data.decode("utf-8")

        client = Client(username, password)
        client.messages.create(from_=phone, to=personal, body=message)


if __name__ == "__main__":
    main()
