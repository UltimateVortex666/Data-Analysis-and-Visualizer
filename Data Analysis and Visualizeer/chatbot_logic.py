import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import uuid
import os
import re

def handle_user_input(message, df, static_folder):
    if df is None:
        return "Please upload a CSV file first.", None

    message = message.lower()

    if "null" in message:
        nulls = df.isnull().sum()
        return f"Null values per column:\n{nulls.to_string()}", None

    elif "columns" in message:
        return f"Columns in dataset: {', '.join(df.columns)}", None

    elif "shape" in message or "size" in message:
        return f"The dataset has {df.shape[0]} rows and {df.shape[1]} columns.", None

    elif "describe" in message:
        return f"Description:\n{df.describe().to_string()}", None

    elif "dtypes" in message or "data types" in message:
        return f"Data types:\n{df.dtypes.to_string()}", None

    elif "unique" in message:
        return f"Unique values:\n{df.nunique().to_string()}", None

    elif "correlation heatmap" in message:
        numeric_df = df.select_dtypes(include='number')
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", cmap="coolwarm")
        filename = f"{uuid.uuid4().hex}_heatmap.png"
        path = os.path.join(static_folder, filename)
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        return "Here is the correlation heatmap.", f"/uploads/{filename}"

    elif "pairplot" in message:
        numeric_df = df.select_dtypes(include='number')
        sns.pairplot(numeric_df.iloc[:, :5])  # Limit to first 5 columns
        filename = f"{uuid.uuid4().hex}_pairplot.png"
        path = os.path.join(static_folder, filename)
        plt.savefig(path)
        plt.close()
        return "Here is the pairplot of the first few numeric columns.", f"/uploads/{filename}"

    elif "correlation" in message:
        return f"Correlation matrix:\n{df.corr(numeric_only=True).to_string()}", None

    elif "extract" in message or "sample" in message:
        col = extract_column_name(message, df)
        if col:
            return df[col].dropna().head(10).to_string(index=False), None
        return "Please specify a valid column to extract data from.", None

    elif "sort by" in message:
        col = extract_column_name(message, df)
        if col:
            sorted_df = df.sort_values(by=col, ascending=True)
            return f"Sorted data (top 10 by '{col}'):\n{sorted_df[[col]].head(10).to_string(index=False)}", None
        return "Please specify a valid column to sort by.", None

    elif "filter" in message or "greater than" in message or "less than" in message:
        col = extract_column_name(message, df)
        if col and pd.api.types.is_numeric_dtype(df[col]):
            try:
                if "greater than" in message:
                    val = float(re.search(r"greater than ([\d\.]+)", message).group(1))
                    filtered_df = df[df[col] > val]
                elif "less than" in message:
                    val = float(re.search(r"less than ([\d\.]+)", message).group(1))
                    filtered_df = df[df[col] < val]
                else:
                    return "Please use 'greater than' or 'less than' with a numeric value.", None

                return f"Filtered rows where '{col}' meets condition:\n{filtered_df[[col]].head(10).to_string(index=False)}", None
            except Exception as e:
                return "Couldn't parse the numeric value for filtering. Please try again.", None
        return "Please specify a valid numeric column to filter.", None

    elif "value counts" in message:
        col = extract_column_name(message, df)
        if col:
            counts = df[col].value_counts().head(10)
            return f"Top value counts in '{col}':\n{counts.to_string()}", None
        return "Please specify a valid column to show value counts.", None

    elif "top" in message:
        try:
            n = int([s for s in message.split() if s.isdigit()][0])
        except:
            n = 5
        return f"Top {n} rows:\n{df.head(n).to_string(index=False)}", None

    elif "visualize" in message or "plot" in message or "graph" in message:
        col = extract_column_name(message, df)
        if col:
            df_col = df[col].dropna()
            fig, axs = plt.subplots(2, 2, figsize=(10, 8))
            sns.histplot(df_col, ax=axs[0, 0], kde=True)
            axs[0, 0].set_title(f'Histogram of {col}')

            sns.boxplot(x=df_col, ax=axs[0, 1])
            axs[0, 1].set_title(f'Boxplot of {col}')

            sns.violinplot(x=df_col, ax=axs[1, 0])
            axs[1, 0].set_title(f'Violin plot of {col}')

            df_col.value_counts().head(10).plot(kind='bar', ax=axs[1, 1])
            axs[1, 1].set_title(f'Bar chart (Top 10) of {col}')

            plt.tight_layout()
            filename = f"{uuid.uuid4().hex}.png"
            path = os.path.join(static_folder, filename)
            plt.savefig(path)
            plt.close()
            return f"Here is the visualization of column '{col}'.", f"/uploads/{filename}"
        return "Please specify a valid column name to visualize.", None

    else:
        return (
            "I can help with data analysis and visualization. Try asking about:\n"
            "- 'null values', 'describe', 'shape', 'data types'\n"
            "- 'visualize <column>', 'correlation heatmap', 'pairplot'\n"
            "- 'sort by <column>', 'filter <column> greater than <value>'\n"
            "- 'value counts of <column>', 'top 5 rows'\n"
        ), None

def extract_column_name(msg, df):
    msg = msg.lower()
    for col in df.columns:
        if col.lower() in msg:
            return col
    # Fallback: match partial words
    words = re.findall(r'\w+', msg)
    for col in df.columns:
        for word in words:
            if word in col.lower():
                return col
    return None
