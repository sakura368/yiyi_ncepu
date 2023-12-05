#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import mph
import os

count = 1
rpath = 'D:\\VSCode_Code\\MPh'
cpath = 'D:\\VSCode_Code\\MPh'
rmc = 'RMC.exe'
modelname = 'ban600x600'
initialname = 'JRR-3M00'
criticalpower = 1305
inpname = initialname

client = mph.start()

while count <= 5:
    print(f'Ready to start No.{count} cycle')

    pymodel = client.load(modelname)
    model = pymodel.java
    
    model.param().set('count', str(count))

    if count >= 2:
        model.func('int1').discardData()
        model.func('int1').set('source', 'file')
        model.func('int1').set('filename', f'{cpath}\\{inpname}.Tally')
        model.func('int1').set('nargs', str(3))
        model.func('int1').importData()

    model.study('std1').run()

    if count == 1:
        model.result().export('data1').set('filename', f'{rpath}\\data1')
        model.result().export('data2').set('filename', f'{rpath}\\data2')

    model.result().export('data1').run()
    model.result().export('data2').run()
    model.result().numerical('av1').run()
    model.result().table('tbl1').comments('ave1 {av1} (MW/m^3)')
    model.result().numerical('av1').set('table', 'tbl1')
    model.result().numerical('av1').setResult()
    model.result().export('tbl1').run()

    with open(f'{cpath}\\table1.txt', 'r+', encoding='utf-8') as fid0:
        for tline in fid0:
            if tline.strip() and '%' not in tline:
                print(tline)
                table = float(tline)
                print(table)
                print(str(count))
                dvpower = table
                print(dvpower)

    pymodel.save(f'{cpath}\\{modelname}')
    client.clear()
    
    # 修正"data2"文件
    data2 = []
    datanum = 0
    with open(f'{rpath}\\data2', 'r+', encoding='utf-8') as fid4:
        for tline in fid4:
            if tline.strip():
                if 'NaN' in tline:
                    tline = tline.replace('NaN', '0')
                data2.append(tline)
                datanum += 1
    with open(f'{rpath}\\data2', 'w+') as fid4:
        for i in range(datanum):
            fid4.write(str(data2[i]) + '\n')

    print('COMSOL run over')

    # 保留tally文件
    if count >= 2:
        os.rename(f'{inpname}.Tally', f'{inpname}_{count - 1}.Tally')

    # 运行RMC
    os.system(f'{rpath}\\{rmc} {inpname}')
    
    print('RMC run over')

    # 读取out文件，记录keff
    keff = []
    with open(f'{cpath}\\{inpname}.out', 'r', encoding='utf-8') as fid1:
        for tline in fid1:
            if tline.strip() and tline.startswith('Final'):
                keff.append(float(tline[12:20]))
                break
    with open(f'{cpath}\\keff.txt', 'a', encoding='utf-8') as keffFile:
        keffFile.write(str(keff) + '\n')

    print('Keff has been recorded')

    # 读取Tally文件
    burnup = np.zeros((100, 100, 100))
    with open(f'{rpath}\\{inpname}.Tally', 'r+', encoding='utf-8') as fid3:
        for tline in fid3:
            if tline.strip() and 'i' not in tline:
                xb = int(tline[0:3])
                yb = int(tline[7:10])
                zb = int(tline[14:17])
                burnup[xb, yb, zb] = float(tline[33:48])
    
    # 修改点功率值，叠加燃耗作为COMSOL功率
    num0 = (burnup != 0)
    burnupave = np.sum(burnup) / np.sum(num0)
    repower = criticalpower * (burnup / burnupave)
    repower = repower * (criticalpower / dvpower)

    # 更新功率文件
    with open(f'{rpath}\\{inpname}.Tally', 'w+', encoding='utf-8') as fid3:
        for x in range(1, xb + 1):
            for y in range(1, yb + 1):
                for z in range(1, zb + 1):
                    newburnup = f'{x:03d}    {y:03d}    {z:03d}                    {repower[x, y, z]:.5e}'
                    fid3.write(newburnup + '\n')

    # 保留data、out文件
    os.rename('data1', f'data1_{count}')
    os.rename('data2', f'data2_{count}')
    os.rename(f'{inpname}.out', f'{inpname}_{count}.out')
    
    print(f'No.{count} cycle has ended')
    
    count += 1  #本循环结束，准备下次循环

print('End of iteration')