import requests
from collections import defaultdict
import time

# Map country codes to simplified continents
continent_map = {
    "US": "NA", "CA": "NA", "MX": "NA",
    "BR": "SA", "AR": "SA", "CL": "SA",

    "GB": "EU", "DE": "EU", "FR": "EU", "IT": "EU", "ES": "EU",
    "RU": "EU", "UA": "EU", "NL": "EU", "PL": "EU",

    "IN": "AS", "CN": "AS", "JP": "AS", "PK": "AS", "SG": "AS",
    "KR": "AS", "ID": "AS", "IR": "AS", "SA": "AS", "TR": "AS",

    "NG": "AF", "ZA": "AF", "EG": "AF", "KE": "AF", "MA": "AF",
}

# Groups
GROUP_A = {"NA", "SA"}
GROUP_B = {"EU", "AS", "AF"}

# Store history for fast movement detection
node_history = []

def fetch_node_distribution():
    try:
        url = "https://bitnodes.io/api/v1/snapshots/latest/"
        response = requests.get(url, timeout=5)
        data = response.json()
        raw_nodes = data["nodes"]

        # Count nodes by continent
        continent_counts = defaultdict(int)
        for node in raw_nodes.values():
            country_code = node[1]
            continent = continent_map.get(country_code)
            if continent:
                continent_counts[continent] += 1

        return continent_counts
    except Exception as e:
        print(f"[Bitnode] Fetch error: {e}")
        return None

def is_fast_movement(current, previous, threshold_percent=2.0):
    if previous == 0:
        return False
    change = ((current - previous) / previous) * 100
    return change >= threshold_percent

def get_bitnode_signal():
    print("Bitnode signal function is running...")
    global node_history

    counts = fetch_node_distribution()
    if not counts:
        return "N/A", "Bitnode: No Signal"

    group_a_count = sum(counts[cont] for cont in GROUP_A if cont in counts)
    group_b_count = sum(counts[cont] for cont in GROUP_B if cont in counts)

    total_nodes = group_a_count + group_b_count
    node_history.append((group_a_count, group_b_count))
    if len(node_history) > 3:
        node_history.pop(0)

    if len(node_history) < 2:
        return f"{total_nodes:,} nodes", "Bitnode Activity: No Signal"

    prev_a, prev_b = node_history[-2]
    fast_a = is_fast_movement(group_a_count, prev_a)
    fast_b = is_fast_movement(group_b_count, prev_b)

    # Activity Logic
    if (fast_a or fast_b) and total_nodes > 10000:
        activity = "High Activity"
    elif not fast_a and not fast_b:
        activity = "Low Activity"
    else:
        activity = "Moderate Activity"

    return f"{total_nodes:,} nodes", f"Bitnode Activity: {activity}"
