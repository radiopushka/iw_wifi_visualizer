#!/usr/bin/python
import re
import sys
import subprocess
import matplotlib.pyplot as plt
#Evan Nikitin 2025 & Deepseek AI assitant

G2_channels = [2412,2417,2422,2427,2432,2437,2442,2447,2452,2457,2462,2467,2472,2482]
G5_channels = [5000 + 5 * ch for ch in [4,8,12,16,20,24,28,32,36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]]
def parse_iwlist_scan(output):
    networks = []
    networks5G = []
    # Split the output into sections for each access point
    sections = re.split('\nBSS ', output)[1:]

    for section in sections:
        # Extract ESSID (network name)
        # SSID: NETGEAR63

        essid_match = re.search(r'SSID:\s*([^\n]+)', section, re.IGNORECASE)
        if essid_match:
            essid = essid_match.group(1).strip()
        else:
            essid = "Unknown"

        #bandwidth
        #channel width:
        width = re.search(r"channel width[=:\s]*(-?\d+\.?\d*)\s*", section, re.IGNORECASE)
        chwidth = 20.0
        if width:
            chwidth = float(width.group(1))
            if chwidth == 1 or chwidth == 0:
                chwidth = 20.0
        # Extract channel
        # freq: 5805.0
        channel = re.search(r"(?:primary channel|Channel)[=:\s]*(-?\d+\.?\d*)\s*", section, re.IGNORECASE)

        freq = re.search(r"(?:freq|Frequency)[=:\s]*(-?\d+\.?\d*)\s*", section, re.IGNORECASE)


        # Extract Signal level in dBm
        # signal: -83.00 dBm
        signal_match = re.search(r"(?:signal|Signal level)[=:\s]*(-?\d+\.?\d*)\s*dBm", section, re.IGNORECASE)
        if not signal_match:
            continue
        signal_dbm = 100+float(signal_match.group(1))
        if(signal_dbm < 0):
            signal_dbm = 0;

        if(float(freq.group(1)) > 4000):
            networks5G.append((essid, signal_dbm, int(channel.group(1)) , float(freq.group(1)),chwidth))
        else:
            networks.append((essid, signal_dbm, int(channel.group(1)) , float(freq.group(1)),chwidth))

    return networks, networks5G

def indexs_in_range(array,min,max):
    indexes = []
    for net in array:
        if net >= min and net <= max:
            indexes.append(array.index(net))
    return indexes



def find_clear_channel(networks,array):
    noise_floor = []
    congestion = []
    total_score = []
    for freq in array:
        noise_floor.append(0)
        congestion.append(0)
        total_score.append(0)
    essids, signals, channels, freqs, cwidths = zip(*networks)
    for signal, freq, cwidth in zip(signals,freqs,cwidths):
        mod_top = freq+cwidth/2
        mod_bottom = freq-cwidth/2
        chnls_used = indexs_in_range(array,mod_bottom,mod_top)
        for chnl in chnls_used:
            congestion[chnl] += 1
            flr = noise_floor[chnl]
            if signal > flr:
                noise_floor[chnl] = signal
            total_score[chnl] += signal
    i = 0
    for cn in congestion:
        if cn != 0:
            total_score[i] /= cn
        i = i + 1
    return noise_floor,congestion,total_score

def are_rectangles_colliding(r1x, r1y, r1w, r1h, r2x, r2y, r2w, r2h):
    # Check for overlap on the x-axis
    x_overlap = max(0, min(r1x + r1w, r2x + r2w) - max(r1x, r2x))
    # Check for overlap on the y-axis
    y_overlap = max(0, min(r1y + r1h, r2y + r2h) - max(r1y, r2y))

    return x_overlap > 0 and y_overlap > 0
def trim_string(text, max_length):
    if len(text) > max_length:
        return text[:max_length]
    else:
        return text
def main():
    if len(sys.argv) < 2:
        print("run: iw dev wlan0 scan > wifi_scan and then supply ./wifi_scan as an argument")
        return

    try:
        with open(sys.argv[1], "r") as file:
            output = file.read()
    except FileNotFoundError:
        print("run: iw dev wlan0 scan > wifi_scan and then supply ./wifi_scan as an argument")
        print("Error: The file was not found.")
        return;
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return;




    networks,networks5G = parse_iwlist_scan(output)


    # Sort networks by channel
    networks.sort(key=lambda x: x[1], reverse=True)
    networks5G.sort(key=lambda x: x[1], reverse=True)

    noise_floor,congestion,total_score = find_clear_channel(networks,G2_channels)
    noise_floor5,congestion5,total_score5 = find_clear_channel(networks5G,G5_channels)

    # Prepare data for plotting
    essids, signals, channels, freqs, cwidths = zip(*networks)
    essids5, signals5, channels5, freqs5, cwidths5 = zip(*networks5G)



    # Create bar chart
    #plt.figure(figsize=(12, 6))
    fig, axs = plt.subplots(2,2)
    axs[0,0].set_xlim(2400,2492);
    axs[0,1].set_xlim(2400,2492);
    axs[1,0].set_xlim(5000,5950);
    axs[1,1].set_xlim(5000,5950);

    for freq in G2_channels:
        axs[0,0].axvline(x=freq, color='blue', linestyle='--', label='ch',alpha=0.3)
        axs[0,1].axvline(x=freq, color='blue', linestyle='--', label='ch',alpha=0.3)
    for freq in G5_channels:
        axs[1,0].axvline(x=freq, color='blue', linestyle='--', label='ch',alpha=0.3)
        axs[1,1].axvline(x=freq, color='blue', linestyle='--', label='ch',alpha=0.3)

    axs[0,1].bar(G2_channels, total_score, color='blue',width = 5,alpha=0.5);
    axs[0,1].bar(G2_channels, congestion, color='red',width = 5,alpha=0.5);
    axs[1,1].bar(G5_channels, total_score5, color='blue',width = 20,alpha=0.5);
    axs[1,1].bar(G5_channels, congestion5, color='red',width = 20,alpha=0.5);

    bars2G = axs[0,0].bar(freqs, signals, color='skyblue',width = 20)
    bars5G = axs[1,0].bar(freqs5, signals5, color='skyblue',width = 160)

    axs[0,1].set_ylabel('Conjestion(red) Avg Signal(blue)')
    axs[1,1].set_ylabel('Conjestion(red) Avg Signal(blue)')
    axs[0,1].set_xlabel('channel')
    axs[1,1].set_xlabel('channel')

    # Customize the plot
    axs[0,0].set_xlabel('channel')
    axs[1,0].set_xlabel('channel')
    axs[0,0].set_ylabel('Signal Quality')
    axs[1,0].set_ylabel('Signal Quality')
    axs[0,0].grid(axis='y', linestyle='--', alpha=0.7)
    axs[1,0].grid(axis='y', linestyle='--', alpha=0.7)

    max_sig = 0;
    for sig in signals:
        if sig > max_sig:
            max_sig = sig

    tv = max_sig/14.0
    axs[0,0].set_ylim(0,max_sig+tv)

    G2_laps = []
    for freq in G2_channels:
        G2_laps.append([])
    for bar, signal, essid, width in zip(bars2G, signals, essids,cwidths):
        sval = signal - 100;
        r = (50-signal)/50;
        g = signal/50;
        bar.set_color((max(0.0,min(r,1.0)),max(0.0,min(g,1.0)),0,0.3))
        bar.set_width(width)


        channels = indexs_in_range(G2_channels,bar.get_x()+5,bar.get_x()+15)
        overlap = 1
        drw = bar.get_height() - tv
        attempts  = 0;
        while overlap == 1 and attempts < 1000:
            overlap = 0
            attempts += 1
            for c in channels:
                for lid in G2_laps[c]:
                    if are_rectangles_colliding(bar.get_x(),drw,20,tv,bar.get_x(),lid,20,tv):
                        if lid - tv/2 <= drw:
                            drw = lid - tv
                        else:
                            drw = drw - tv;
                        if(drw < 0):
                            drw = max_sig
                        overlap = 1



        for c in channels:
            G2_laps[c].append(drw)
        essid = trim_string(essid,22);
        axs[0,0].annotate(f'{sval} dBm\n{essid}', xy=(bar.get_x(),drw),fontsize = 3)
    G5_laps = []

    max_sig = 0;
    for sig in signals5:
        if sig > max_sig:
            max_sig = sig

    tv = max_sig/14.0
    axs[1,0].set_ylim(0,max_sig+tv)

    for freq in G5_channels:
        G5_laps.append([])
    for bar, signal, essid, width in zip(bars5G, signals5, essids5,cwidths5):
        sval = signal - 100;
        r = (50-signal)/50;
        g = signal/50;
        bar.set_color((max(0.0,min(r,1.0)),max(0.0,min(g,1.0)),0,0.3))

        bar.set_width(width)

        channels = indexs_in_range(G5_channels,bar.get_x()+5,bar.get_x()+155)
        overlap = 1
        drw = bar.get_height() - tv
        attempts  = 0;
        while overlap == 1 and attempts < 1000:
            overlap = 0
            attempts += 1
            for c in channels:
                for lid in G5_laps[c]:
                    if are_rectangles_colliding(bar.get_x(),drw,160,tv,bar.get_x(),lid,160,tv):
                        if lid - tv/2 <= drw:
                            drw = lid - tv
                        else:
                            drw = drw - tv;
                        if(drw < 0):
                            drw = max_sig
                        overlap = 1



        for c in channels:
            G5_laps[c].append(drw)

        essid = trim_string(essid,18);
        axs[1,0].annotate(f'{sval} dBm\n{essid}', xy=(bar.get_x(), drw),fontsize = 3)

    plt.tight_layout()
    plt.savefig("WIFI_GRAPH.png",dpi = 300)
    print("Wifi statistics saves to WIFI_GRAPH.png")

if __name__ == "__main__":
    main()
