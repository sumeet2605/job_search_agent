from config import MAX_RESULTS_TO_WRITE, MIN_WRITE_SCORE, SHEET_NAME, SPREADSHEET_ID
from scoring import should_write
from sheets_client import append_unique, get_service, setup_workbook
from sources import collect_jobs


def main():
    print(f"Using spreadsheet={SPREADSHEET_ID}, primary_sheet={SHEET_NAME}, min_score={MIN_WRITE_SCORE}")
    service = get_service()
    setup_workbook(service)

    jobs = collect_jobs()
    jobs = jobs[:MAX_RESULTS_TO_WRITE]
    recommended = [j for j in jobs if should_write(j, MIN_WRITE_SCORE)]
    top_recommended = [j for j in recommended if j.get("priority") in ("P1", "P2")]

    for j in jobs:
        print(f"Candidate score={j['score']} priority={j['priority']} portal={j['portal']} title={j['title'][:120]}")

    added_all = append_unique(service, SHEET_NAME, jobs)
    added_rec = append_unique(service, "Recommended", top_recommended)
    print(f"Found {len(jobs)} candidate jobs; added_all={added_all}; recommended={len(top_recommended)}; added_recommended={added_rec}")


if __name__ == "__main__":
    main()
