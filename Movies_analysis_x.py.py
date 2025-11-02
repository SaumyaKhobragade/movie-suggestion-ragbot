import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df=pd.read_csv("movies_dataset.csv")

df.head()

df.tail()

x=df.info()
print(x)

print(df.describe())

df.isnull().sum()

plt.figure(figsize=(10, 8))
avg_profit_genre = df.groupby("genre")["Profit"].mean().sort_values(ascending=False).head(10)
sns.barplot(x=avg_profit_genre.index, y=avg_profit_genre.values,)
plt.title("Top 10 Genres by Average Profit")
plt.ylabel("Average Profit")
plt.xlabel("Genres")
plt.show()

plt.figure(figsize=(10, 8))
sns.scatterplot(x="Budget", y="Profit", data=df, hue="genre")
plt.title("Profit by Budget of Genre")
plt.xlabel("Budget")
plt.ylabel("Profit")
plt.show()

plt.figure(figsize=(12, 6))
sns.lineplot(x="Release Year", y="Revenue", data=df, label="Revenue", color="blue")
sns.lineplot(x="Release Year", y="Profit", data=df, label="Profit", color="green")
plt.title("Revenue and Profit Trends Over the Years")
plt.ylabel("Amount")
plt.show()

plt.figure(figsize=(8, 6))
sns.heatmap(df[["Budget", "Revenue", "Profit"]].corr(), annot=True)
plt.title("Correlation Heatmap")
plt.show()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Movie Dataset Analysis", fontsize=20)
###Distribution of Profit
sns.histplot(df["Profit"], bins=30, kde=True, color="skyblue", ax=axes[0, 0])
axes[0, 0].set_title("Profit Distribution")
axes[0, 0].set_xlabel("Profit")
axes[0, 0].set_ylabel("Frequency")
###Average Profit by Genre
avg_profit = df.groupby("genre")["Profit"].mean().sort_values(ascending=False).head(10)
sns.barplot(x=avg_profit.values, y=avg_profit.index, ax=axes[0, 1])
axes[0, 1].set_title("Top 10 Genres by Average Profit")
axes[0, 1].set_xlabel("Average Profit")
axes[0, 1].set_ylabel("Genre")
###Profit vs Budget Scatter
sns.scatterplot(data=df, x="Budget", y="Profit", ax=axes[1, 0],hue="genre")
axes[1, 0].set_title("Profit vs Budget by Genre")
axes[1, 0].set_xlabel("Budget")
axes[1, 0].set_ylabel("Profit")
### Trend of Revenue and Profit Over Years
trend = df.groupby("Release Year")[["Revenue", "Profit"]].mean().reset_index()
sns.lineplot(data=trend, x="Release Year", y="Revenue", label="Revenue", ax=axes[1, 1], color="blue", linewidth=2.5)
sns.lineplot(data=trend, x="Release Year", y="Profit", label="Profit", ax=axes[1, 1], color="green", linewidth=2.5)
axes[1, 1].set_title("Revenue Profit Trend Over Years")
axes[1, 1].set_xlabel("Release Year")
axes[1, 1].set_ylabel("Amount")
axes[1, 1].legend()
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.show()

