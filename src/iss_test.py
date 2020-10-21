import numpy as np
import pyOER
import ISS # from github:Ejler/DataTreatment
import common_toolbox as ct # from github:Ejler/DataTreatment
import matplotlib.pyplot as plt
###
samples = {}
# RuO2
samples['RuO2 amorphous'] = [
    'Nancy1',# 16
    'Nancy5',# 16
    'Nancy6',# 16
    'Easter1A',#    18
    'Easter1B',#    18
    'Easter1C',#    18
    'Taiwan1A',#    18
    'Taiwan1C',#    18
    'Taiwan1G',#    18
    'Taiwan1D',#    18
]
samples['RuO2 rutile'] = [
    'Reshma4E',# 16 (400 C)
    'Reshma4F',# 16 (400 C)
    'Reshma4I',# 16 (400 C)
    'Stoff4E',#    18
    'Stoff4F',#    18
    'Stoff4A',#    18
    'Stoff4B',#    18
    'Stoff1D',#    18
    'John4A',#    18
    'John4C',#    18
]
samples['Ru foam'] = [
    'Evans9',# 16
    'Evans7',# 16
    'Evans2',# 16
    'Evans8',# 16
    'Evans12',# 16
]
samples['Ru metallic'] = [
    'Bernie4',# EC-treated
    'Bernie5',# EC-treated
    'Melih2',# treated
]
# Pt
samples['Pt'] = [
    'Trimi1',
]
# Ir (all)
samples['Ir'] = [
    'Jazz5',# EC-treated (metallic)
    'Folk3',# EC-treated (rutile)
    'Goof1A',# RT 18
    'Goof1B',# RT 18
    'Legend4A',# 400C 18
    'Legend4C',# 400C 18
    'Decade1A',# RT 18
    'Decade1G',# RT 18
    'Decade1B',# RT 18
    'Decade1C',# RT 18
]

#samples = ['Reshma', 'Stoff', 'Easter', 'Bernie', 'Melih'] # for testing
#title, samples = 'Oxygen content 1', ['Nancy', 'Trimi', 'Evans', 'Bernie', 'Melih', 'Reshma', 'Easter', 'Jazz', 'Folk', 'Goof']
#title, samples = 'Oxygen content 2', ['Stoff', 'Taiwan', 'John', 'Legend', 'Decade']

# Choose selected groups here ### SELECTION ###
selection = [
    #'RuO2 amorphous',
    #'RuO2 rutile',
    'Ru foam',
    #'Pt',
]
title = 'RuO2 foam'

colors = ['k', 'r', 'g', 'b', 'm']*10
invalid_samples = []
datas = {}
ratios = {}
names = [sample_ for selected in selection for sample_ in samples[selected]]
for sample_counter, sample in enumerate(names):
    data = pyOER.ISS(sample)
    if len(data.keys) == 0:
        print(f'Could not find data matching "{sample}"')
        invalid_samples.append(sample_counter)
        continue
    datas[sample] = data
    print('*'*20)
    print(f'Available keys: {data.keys}')
    ISS.align_spectra(data._active.values())
    ratios[sample], coeffs = data.fit_with_reference(peaks=[[16, 18]], plot=False)
    for i in ratios[sample].keys():
        if data._active[i].good is False:
            continue
        print(data._active[i].filename)
        print(data._active[i].date)
        print(f'\nOxygen 16 content: {ratios[sample][i]["16"]*100} %\n')

# Remove invalid samples from list
invalid_samples.reverse()
for i in invalid_samples:
    sample = names.pop(i)
    print(f'Could not find data matching "{sample}"')

def date_formatter(date):
    """Take datetime object and return string of YYADD"""
    YY = date.year - 2000
    M = date.month
    DD = date.day
    hh = date.hour
    mm = date.minute
    ss = date.second
    translate = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g',
        8: 'h', 9: 'i', 10: 'j', 11: 'k', 12: 'l'}
    string = f"{YY}{translate[M].upper()}{DD} {hh}:{mm}:{ss}"
    string = r"$\bf{" + f"{YY}{translate[M].upper()}{DD}" + r"}$" + f"   {hh}:{mm}:{ss}"
    return string

# Plot all O-16 ratios
plot_data = []
counter = 0
fig = plt.figure(title)
ax = fig.add_axes([0.05, 0.15, 0.9, 0.6])
for j, sample in enumerate(names):
    for i in datas[sample].keys:
        # Skip bad data
        if datas[sample]._active[i].good is False:
            continue
        # Plot good data
        plt.plot(counter, ratios[sample][i]['16']*100, 'o', color=colors[j])
        plot_data.append([
            sample,
            datas[sample],
            datas[sample]._active[i].sample,
            datas[sample]._active[i].date,
            counter,
            ratios[sample][i]['16'],
            ratios[sample][i]['18'],
        ])
        counter += 1
xticks = [i for (gen_name, data_object, name, date, i, r1, r2) in plot_data]
dates = [date_formatter(date) for (gen_name, data_object, name, date, i, r1, r2) in plot_data]
xlabels = [f'{gen_name} {name.lstrip(gen_name)}' for (gen_name, data_object, name, date, i, r1, r2) in plot_data]

secaxx = ax.secondary_xaxis('top')
secaxy = ax.secondary_yaxis('right')

# Update canvas
fig.canvas.draw()

secaxy.set_ylabel('O-18 ratio (%)')
#ylabels2 = [item.get_text() for item in secaxy.get_yticklabels()]
#ylabels2.reverse()
yticks = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
ax.set_yticks(yticks)
ax.set_yticklabels(yticks)
secaxy.set_yticks(yticks)
yticks.reverse()
secaxy.set_yticklabels(yticks)
#secaxy.set_yticklabels(ylabels2)
secaxx.set_xticks(xticks)
secaxx.set_xticklabels(dates, rotation=90, fontsize=12)
ax.set_xticks(xticks)
ax.set_xticklabels(xlabels, rotation=90, fontsize=12)
ax.set_ylabel('O-16 ratio (%)')
plt.grid(True)
plt.show()
"""
 x   1) import the reference data into pyOER (easy)
 x   2) modify the fitting method to account for the new structure (semi-easy)
     3) throw the omicron data in the mix with the rest (semi-easy)
"""

#data.plot()

"""
#ISS.align_spectra(data._active.values())

ratios, coeffs = data.fit_with_reference(peaks=[[16, 18]], plot=False)
plt.figure('Break')

ref1 = data._ref['thetaprobe'][16]['peak']
ref2 = data._ref['thetaprobe'][18]['peak']

# Raw + background
plt.plot(data._active[0].shifted['oxygen'], data._active[0].y, 'k-')
plt.plot(data._active[0].shifted['oxygen'], data.background[0], 'k:')

# Fit
plt.plot(data._active[0].shifted['oxygen'], data.background[0] + ref1*coeffs[0][16] + ref2*coeffs[0][18], 'y-')
plt.plot(data._ref['thetaprobe'][16]['xy'][:, 0], data.background[0] + ref1*coeffs[0][16] + ref2*coeffs[0][18], 'b-')

#plt.plot(data._ref['thetaprobe'][16]['xy'][:, 0], data._ref['thetaprobe'][16]['xy'][:, 1], 'r-')
#plt.plot(data._active[0].shifted['oxygen'], data.background[0] + ref1*coeffs[0][16], 'r:')
plt.plot(data._ref['thetaprobe'][16]['xy'][:, 0], ref1, 'r-')
#plt.plot(data._ref['thetaprobe'][18]['xy'][:, 0], data._ref['thetaprobe'][18]['xy'][:, 1], 'g-')
plt.plot(data._ref['thetaprobe'][18]['xy'][:, 0], ref2, 'g-')

#data.plot(show=False)

data._active[0].AddMassLines([16, 18, 101])
data.show()

#for i in data.keys:
#    print(i, ratios[i]['16'])
"""
