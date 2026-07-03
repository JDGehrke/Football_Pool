# -*- coding: utf-8 -*-
#@author: JG077923

import os
import pandas as pd
import warnings
import pdb
#from ggplot import *
#del chopsticks,diamonds,meat,movies,mpg,mtcars,pageviews,pigeons,salmon

warnings.filterwarnings('ignore')

# =============================================================================
#  Football Pool
# =============================================================================
os.chdir(r'C:\Users\ko164b5\OneDrive - Kohler Co\Documents\Personal Documents\Football Pool')

season = '2025-2026'
week = 22

# =============================================================================
#  Weekly Picks
# =============================================================================
#weekDict={1:'1',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:'10',11:'11',12:'12',13:'13',14:'14',15:'15',16:'16',17:'17',18:'Wild Card',19:'Divisional',20:'Conference',21:'SuperBowl'}
weekDict={1:'1',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:'10',11:'11',12:'12',13:'13',14:'14',15:'15',16:'16',17:'17',18:'18',19:'WildCard',20:'Divisional',21:'Conference',22:'SuperBowl'}

#Reading in the data
df = pd.DataFrame(pd.read_csv(os.getcwd()+'\\'+season+'\\Week'+str(week)+'.csv'))

#Make sure unique number of Picks per person
assert len(df) == len(df['Name'].unique())

#Cleaning the picks sheet
df=df.set_index('Name')
df.loc[df.index != '', 'Score'] = df[df.columns[-1]]+df[df.columns[-2]]
if 'Username' in df.columns:
    df=df.drop(columns=[df.columns[0],df.columns[1],df.columns[-2],df.columns[-3]])
else:
    df=df.drop(columns=[df.columns[0],df.columns[-2],df.columns[-3]])

#Creating the Records table
if week!=1:
    records=pd.DataFrame(columns=['Name','Week','Week(#)','Wins','Losses','Percentage','Score Diff','Place'])
else:
    records=pd.DataFrame(columns=['Name','Week','Week(#)','Wins','Losses','Percentage','Score Diff','Place',
                                  'Overall Wins','Overall Losses','Overall Percentage',
                                  'Overall Place','Place Delta','Games Back','Games Back Delta','Weekly Wins'])

#Looping through to compare results with Winners
for p in df.index:
    if p=='Winners':
        pass
    else:
        wins=0
        losses=0
        scoreAbs=0
        for col in df:
            if col!='Score':
                if df[col]['Winners']=='Tie':
                    wins+=1
                elif df[col][p]==df[col]['Winners']:
                    wins+=1 
                else:
                    losses+=1 
        scoreAbs=-1*(abs(df['Score']['Winners']-df['Score'][p]))
        # records=records.append({'Name':p,
        #                         'Week':weekDict[week],
        #                         'Week(#)':week,
        #                         'Wins':wins,
        #                         'Losses':losses,
        #                         'Percentage':round(wins/(wins+losses),2),
        #                         'Score Diff':scoreAbs},ignore_index=True)
        
        row = pd.DataFrame.from_dict({'Name':p,
                                        'Week':weekDict[week],
                                        'Week(#)':week,
                                        'Wins':wins,
                                        'Losses':losses,
                                        'Percentage':round(wins/(wins+losses),2),
                                        'Score Diff':scoreAbs},orient='index').T #Transpose dataframe
        
        records = pd.concat([records,row])
    
del p,col,wins,losses,scoreAbs,weekDict,row

#Organizing based on Wins first followed by smallest score differential
records=records.sort_values(by=['Wins','Score Diff'],ascending=False).reset_index(drop=True)

#Giving placements based off Wins and Score differential
plc=1
lastWins=0
lastScoreDiff=0
lastplc=0
for p in records.index:
    if records['Wins'][p]==lastWins and records['Score Diff'][p]==lastScoreDiff:
        records['Place'][p]=lastplc
    else:
        records['Place'][p]=plc
    plc+=1
    lastWins=records['Wins'][p]
    lastScoreDiff=records['Score Diff'][p]
    lastplc=records['Place'][p]
del plc,lastWins,lastScoreDiff,lastplc,p

# =============================================================================
# Overall Sections
# =============================================================================
if week==1:
    records['Overall Wins']=records['Wins']
    records['Overall Losses']=records['Losses']
    records['Overall Percentage']=records['Overall Wins']/(records['Overall Wins']+records['Overall Losses'])
    records['Overall Place']=records['Place']
    
    #Calculating Place Delta
    if (len(df)-1)%2 == 0: #even
        records['Place Delta']=((len(df)-1)//2)-records['Overall Place']
    else: #odd
        records['Place Delta']=(((len(df)-1)//2)+1)-records['Overall Place']
        
    #Calculating Games Back
    maxWins = records.loc[records['Place']==1]['Wins'].max()
    records['Games Back'] = records['Wins'].apply(lambda x:maxWins-x)
    records['Games Back Delta'] = records['Games Back'] * -1
    del maxWins
    
    #Increasing Weekly Wins
    records['Weekly Wins']=0
    records.loc[records['Place']==1,'Weekly Wins']=1
    

else:
    concat = pd.DataFrame(pd.read_excel(os.getcwd()+'\\'+season+'\\Season Concat.xlsx',sheet_name='Concat'))
    overall = concat.loc[concat['Week(#)'] == week-1]
    
    overall=overall[['Name','Overall Wins', 'Overall Losses', 'Overall Percentage', 'Overall Place','Place Delta','Games Back','Games Back Delta','Weekly Wins']]
    records = pd.merge(records,overall,on='Name')
    del overall
    
    #Overwriting the Overall numbers
    records['Overall Wins'] = records['Wins'] + records['Overall Wins']
    records['Overall Losses'] = records['Losses'] + records['Overall Losses']
    records['Overall Percentage'] = (records['Overall Wins']/(records['Overall Wins']+records['Overall Losses'])).astype(float).round(2)
    
    #Calculating Place
    records['Place_last_week'] = records['Overall Place']
    records['Overall Place'] = records['Overall Wins'].rank(method='min',ascending=False)
    records['Place Delta'] = records['Place_last_week'] - records['Overall Place']
    
    #Calculating Games Back
    records['Games_back_last_week'] = records['Games Back']
    maxWins = records.loc[records['Overall Place']==1]['Overall Wins'].max()
    records['Games Back'] = records['Overall Wins'].apply(lambda x:maxWins-x)
    records['Games Back Delta'] = records['Games_back_last_week'] - records['Games Back']
    records = records.drop(columns=['Place_last_week','Games_back_last_week'])
    del maxWins
    
    #Increasing Weekly Wins
    records.loc[records['Place']==1,'Weekly Wins']=records['Weekly Wins']+1

# =============================================================================
# Concat File
# =============================================================================
if week==1:
    concat = records.copy()
else:
    #concat = concat.append(records)
    concat = pd.concat([concat,records])
    
# =============================================================================
# CHECK ALL PARTICIPANTS
# =============================================================================
missing_users = [user for user in concat['Name'].unique() if user not in records['Name'].unique()]
if len(missing_users) > 0:
    print(f"Missing users: {missing_users}")
    print('Use ',records.iloc[-1:,:]['Name'])
del missing_users

# =============================================================================
# Breakpoint
# =============================================================================
#breakpoint()


# =============================================================================
# Export Section
# =============================================================================
print('Exporting Files')

#Exporting them all to a monthly excel file
writer=pd.ExcelWriter(os.getcwd()+'\\'+season+'\\Season Concat.xlsx', engine='xlsxwriter')
records.to_excel(writer, sheet_name='Records',index=False)
concat.to_excel(writer, sheet_name='Concat', index=False)
writer.close()


# =============================================================================
# Graph Section
# =============================================================================

# records = pd.DataFrame(pd.read_excel(r"C:\Users\JG077923\OneDrive - Cerner Corporation\Desktop\Football Pool\2021-2022\Season Concat.xlsx",sheet_name='Records'))
# concat = pd.DataFrame(pd.read_excel(r"C:\Users\JG077923\OneDrive - Cerner Corporation\Desktop\Football Pool\2021-2022\Season Concat.xlsx",sheet_name='Concat'))


# #Facet Weekly Line Graph
# g = ggplot(aes(x='Week(#)',y='Percentage'),concat) + geom_point() +geom_line() + facet_wrap('Name') + scale_x_continuous("Week(#)", breaks=list(range(1,week+1)))
# g.save(r"C:\Users\JG077923\OneDrive - Cerner Corporation\Desktop\Football Pool\2021-2022\facet.png")
# display(g)

# #Boxplot of Wins
# g = ggplot(aes(x='Name', y='Percentage'),concat) + geom_boxplot()
# g.save(r"C:\Users\JG077923\OneDrive - Cerner Corporation\Desktop\Football Pool\2021-2022\boxplot.png")
# display(g)

# #Wins scatter with trend
# g = ggplot(aes(x='Week(#)',y='Percentage'),concat) + geom_point() + stat_smooth() + scale_x_continuous("Week(#)", breaks=list(range(1,week+1)))
# g.save(r"C:\Users\JG077923\OneDrive - Cerner Corporation\Desktop\Football Pool\2021-2022\trend.png")
# display(g)



# # =============================================================================
# # For Weekly Win TieBreakers
# # =============================================================================
# from pandasql import sqldf

# weeklywins = sqldf(f'''
#                     SELECT Name,SUM([Score Diff]) as Total_Diff, SUM([Score Diff])/{records['Weekly Wins'].max()} as Avg_Diff
#                     FROM concat
#                     WHERE Name in (SELECT Name FROM records WHERE [Weekly Wins] = {records['Weekly Wins'].max()})
#                     AND Place = 1
#                     GROUP BY NAME
#                     ORDER BY SUM([Score Diff]) desc
                    
#                     ''')
                    


# =============================================================================
# New
# =============================================================================


# import urllib.request


# response = urllib.request.urlopen('https://www.nfl.com/schedules/2022/REG17/',timeout=60)

# text = response.read()

