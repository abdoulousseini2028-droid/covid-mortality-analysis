"""
COVID-19 Mortality Analysis
Analyzes global death rates by continent and correlates with elderly population demographics
Data source: Our World in Data (OWID)
Author: Abdoul Rahim Ousseini
"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

# Load dataset from OWID (Our World in Data)
df = pd.read_csv('owid-covid-data.csv')

# Initial data exploration
print(f"Dataset shape: {df.shape}")
print(df.columns.tolist()[:10])  # Preview first 10 column names
print(df.head(3))

# Set up in-memory SQL database for querying
conn = sqlite3.connect(':memory:')

# Convert date column to datetime format
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Filter data: remove rows without continent info, start from March 2020
df_clean = df[df['continent'].notna()]
df_clean = df_clean[df_clean['date'] >= '2020-03-01']

# Import cleaned data into SQLite table
df_clean.to_sql('covid_data', conn, index=False, if_exists='replace')
print(f"\nLoaded {len(df_clean)} rows into database")

# Query 1: Calculate average deaths per million for each continent
query1 = """
SELECT 
    continent, 
    ROUND(AVG(total_deaths_per_million), 2) as avg_deaths_per_million,
    COUNT(DISTINCT location) as num_countries
FROM covid_data 
GROUP BY continent 
ORDER BY avg_deaths_per_million DESC
"""
deaths_by_continent = pd.read_sql_query(query1, conn)
print("\n=== Deaths per Million by Continent ===")
print(deaths_by_continent)

# Query 2: Get data for correlation analysis (deaths vs elderly population)
query2 = """
SELECT 
    continent,
    ROUND(AVG(total_deaths_per_million), 2) as avg_deaths_per_million,
    ROUND(AVG(aged_65_older), 2) as avg_aged_65_pct
FROM covid_data 
GROUP BY continent
"""
correlation_data = pd.read_sql_query(query2, conn)
print("\n=== Deaths vs Elderly Population % ===")
print(correlation_data)

# Compute Pearson correlation coefficient
corr = correlation_data['avg_deaths_per_million'].corr(correlation_data['avg_aged_65_pct'])
print(f"\nPearson Correlation (Deaths vs % 65+): {corr:.3f}")

# Close database connection
conn.close()

# Visualization 1: Bar chart showing deaths by continent
plt.figure(figsize=(10, 6))
plt.bar(deaths_by_continent['continent'], deaths_by_continent['avg_deaths_per_million'], 
        color='coral')
plt.title('Average COVID Deaths per Million by Continent (2020-2021)', 
          fontsize=14, fontweight='bold')
plt.xlabel('Continent')
plt.ylabel('Deaths per Million')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('deaths_by_continent.png', dpi=150)
print("\nSaved: deaths_by_continent.png")
plt.show()

# Visualization 2: Scatter plot - deaths vs elderly population percentage
plt.figure(figsize=(8, 6))
plt.scatter(correlation_data['avg_aged_65_pct'], 
            correlation_data['avg_deaths_per_million'], 
            s=150, alpha=0.7, color='steelblue')

# Add continent labels to each point
for i, continent in enumerate(correlation_data['continent']):
    plt.annotate(continent, 
                (correlation_data['avg_aged_65_pct'].iloc[i], 
                 correlation_data['avg_deaths_per_million'].iloc[i]),
                fontsize=10, ha='center')

plt.title(f'COVID Deaths vs Elderly Population (Correlation: {corr:.2f})', 
          fontsize=14, fontweight='bold')
plt.xlabel('% Population Aged 65+')
plt.ylabel('Avg Deaths per Million')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('deaths_vs_elderly.png', dpi=150)
print("Saved: deaths_vs_elderly.png")
plt.show()

print("\nAnalysis complete! Charts saved to current directory.")
