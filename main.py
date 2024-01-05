import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import statistics
import json

load_dotenv()

V3 = [
    "Checkout Repository",
    "Checkout Repository Again",
    "Checkout Repository Third Time",
    "Checkout Repository 4th Time",
    "Checkout Repository 5th Time",
]
V4 = [
    "Checkout Repository v4",
    "Checkout Repository v4 Again",
    "Checkout Repository v4 Third Time",
    "Checkout Repository v4 4th Time",
    "Checkout Repository v4 5th Time",
]
USER = os.getenv("GH_USER")
TOKEN = os.getenv("GH_TOKEN")
repo = "Telefonica/baikal-ci-playground"


def calculate_time(started_at, completed_at):
    time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    tiempo_inicio = datetime.strptime(started_at, time_format)
    tiempo_fin = datetime.strptime(completed_at, time_format)

    diferencia = tiempo_fin - tiempo_inicio
    segundos_transcurridos = diferencia.total_seconds()

    return segundos_transcurridos


def analyze_runs(wf_id, runs_to_analyze):
    results = []

    base_url = (
        "https://api.github.com/repos/Telefonica/baikal-ci-playground/actions/workflows"
    )
    runs_url = f"{base_url}/{wf_id}/runs?per_page={runs_to_analyze}"

    # get runs
    response = requests.get(runs_url, auth=(USER, TOKEN))

    if response.status_code == 200:
        runs_data = response.json()

        for run in runs_data["workflow_runs"]:
            jobs_url = run["jobs_url"]

            # get jobs for every run
            jobs_response = requests.get(jobs_url, auth=(USER, TOKEN))

            if jobs_response.status_code == 200:
                jobs_data = jobs_response.json()

                # only 1 job per run
                job = jobs_data["jobs"][0]

                steps = job["steps"]
                v3_times = []
                v4_times = []
                for step in steps:
                    if (
                        step["name"] in V3
                        and step["status"] == "completed"
                        and step["conclusion"] == "success"
                    ):
                        v3_times.append(
                            calculate_time(step["started_at"], step["completed_at"])
                        )
                    elif (
                        step["name"] in V4
                        and step["status"] == "completed"
                        and step["conclusion"] == "success"
                    ):
                        v4_times.append(
                            calculate_time(step["started_at"], step["completed_at"])
                        )

                if v3_times and v4_times:
                    results.append(
                        {
                            "runner_name": job["runner_name"],
                            "runner_id": job["runner_id"],
                            "v3_times": v3_times,
                            "v4_times": v4_times,
                            "started": job["started_at"]
                        }
                    )

                print(f"added result for runner {job['runner_name']}")

            else:
                print(f"No se pudieron obtener los jobs para el run {jobs_url}")

    else:
        print(f"No se pudieron obtener los runs para el workflow {runs_url}")

    return sorted(results, key=lambda x: x["runner_name"])


class WF_IDS:
    large = 81106573
    medium = 81213378
    small = 81213377


def print_results(runs):
    for run in runs:
        print(
            f"{run['runner_name']} - V3 mean: {statistics.mean(run['v3_times'])/60:.2f} - V4 mean: {statistics.mean(run['v4_times'])/60:.2f}"
        )

def guarda_json(diccionario, nombre_archivo):
    with open(nombre_archivo, 'w+') as archivo:
        json.dump(diccionario, archivo, indent=4)  # 'indent' para una visualización más legible


if __name__ == "__main__":
    larges = analyze_runs(WF_IDS.large, 16)
    meds = analyze_runs(WF_IDS.medium, 8)
    smalls = analyze_runs(WF_IDS.small, 8)
    todos = smalls + meds + larges

    print_results(todos)
    guarda_json(smalls, "results/smalls.json")
    guarda_json(meds, "results/mediums.json")
    guarda_json(larges, "results/larges.json")
