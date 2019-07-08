import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from crundb import utils
import datetime


class QueryCHECRunLog:
    def __init__(self, sheetid, tokenfile=None, credfile=None, scopes=None):
        self.creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        self.datafolder = utils.get_data_folder()
        self.tokenfile = tokenfile or os.path.join(self.datafolder, "token.pickle")
        self.credfile = credfile or os.path.join(self.datafolder, "credentials.json")
        # If modifying these scopes, delete the file token.pickle.
        self.scopes = scopes or [
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
        if os.path.exists(self.tokenfile):
            with open(self.tokenfile, "rb") as token:
                self.creds = pickle.load(token)
                print("read token")
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if os.path.exists(self.credfile):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credfile, self.scopes
                    )
                    self.creds = flow.run_local_server()
                else:
                    print(f"no credentials file found at {self.credfile}")
                    raise RuntimeError
            # Save the credentials for the next run
            with open(self.tokenfile, "wb") as token:
                pickle.dump(self.creds, token)
        self.service = build("sheets", "v4", credentials=self.creds)
        # Call the Sheets API
        self.sheet = self.service.spreadsheets()
        self.sheetid = sheetid

    def get_sub_sheet_ids(self):
        sheet_metadata = self.sheet.get(spreadsheetId=self.sheetid).execute()
        sheets = sheet_metadata.get("sheets", "")
        self.sub_sheets = {}
        for sheet in sheets:
            title = sheet.get("properties", {}).get("title", "Sheet1")
            sheet_id = sheet.get("properties", {}).get("sheetId", 0)
            self.sub_sheets[title] = sheet_id
        return self.sub_sheets

    def query(self, sheetid, range_):
        result = (
            self.sheet.values()
            .get(spreadsheetId=self.sheetid, range=range_)  # +'/#gid='+sheetid,
            .execute()
        )
        return result.get("values", [])


def query_chec_runlog():
    chechrunlog = QueryCHECRunLog("1JsddNjCJ6xsGZfSLcxkZ39ArfXt4ryEUDJarfonAH_o")
    subsheets = chechrunlog.get_sub_sheet_ids()
    run_metadata = {}
    for title, sid in subsheets.items():
        if "d2019" not in title:
            continue
        # print(title,sid)
        # print(str(sid)+'!A1:U100')
        values = chechrunlog.query("", str(title) + "!A1:U100")
        fields = values[0]
        runnumberfield = 2
        for row in values[1:]:
            tmpdict = {}
            run_metadata[row[runnumberfield]] = {}
            for i, col in enumerate(row):
                tmpdict[fields[i]] = col

            year, month, day = int(title[1:5]), int(title[6:8]), int(title[9:11])
            tmpdict["obsdate"] = datetime.date(year, month, day)
            duration_str = tmpdict["Approximate Duration (min)"]

            # Deal with human input
            if "s" in duration_str:
                tmpdict["Approximate Duration (min)"] = datetime.timedelta(
                    seconds=int("".join(([d for d in filter(str.isdigit, "123sec")])))
                )
            elif (
                len(duration_str) > 0
                and tmpdict["Approximate Duration (min)"].isdigit()
            ):
                tmpdict["Approximate Duration (min)"] = datetime.timedelta(
                    minutes=int(duration_str)
                )
            else:
                tmpdict["Approximate Duration (min)"] = None
            print(tmpdict["Approximate Start Time"])

            if (
                len(tmpdict["Approximate Start Time"]) > 0
                and ":" in tmpdict["Approximate Start Time"]
            ):
                hour, minute = map(int, tmpdict["Approximate Start Time"].split(":"))
                tmpdict["Approximate Start Time"] = datetime.time(hour, minute)
                if hour < 6:
                    timestamp = datetime.datetime(
                        year, month, day, hour, minute
                    ) + datetime.timedelta(days=1)
                else:
                    timestamp = datetime.datetime(year, month, day, hour, minute)
            else:
                timestamp = None
                tmpdict["Approximate Start Time"] = None
            tmpdict["run_start_timestamp"] = timestamp
            run_metadata[row[runnumberfield]] = tmpdict
    return run_metadata


if __name__ == "__main__":
    query_chec_runlog()
