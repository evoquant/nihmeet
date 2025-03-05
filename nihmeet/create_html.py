import json
import plotly.graph_objs as go
import plotly.offline as pltoff
import pandas as pd


def load_jsonl_data(filepath):
    """
    Load data from a JSONL file.

    Args:
        filepath (str): Path to the JSONL file

    Returns:
        list: List of dictionaries containing meeting data
    """
    with open(filepath, "r") as f:
        return [json.loads(line) for line in f]


def create_dataframe(data):
    """
    Convert loaded data to a pandas DataFrame.

    Args:
        data (list): List of meeting dictionaries

    Returns:
        pandas.DataFrame: Structured meeting data
    """
    return pd.DataFrame(data)

def generate_fed_reg_date_plot(df):
    """
    Create a combined bar and scatter plot of cumulative entries by Federal Register publication date.

    Args:
        df (pandas.DataFrame): Meeting data

    Returns:
        str: HTML for Federal Register date plot
    """
    # Ensure date is parsed correctly
    df['fed_reg_publication_date'] = pd.to_datetime(df['fed_reg_publication_date']).dt.normalize()
    
    # Group by date
    date_counts = df.groupby(df['fed_reg_publication_date'].dt.date).size().reset_index()
    date_counts.columns = ["Date", "Count"]
    date_counts = date_counts.sort_values("Date")

    # Calculate cumulative count
    date_counts["Cumulative_Count"] = date_counts["Count"].cumsum()

    # Convert dates to string for plotting
    date_counts["Date"] = date_counts["Date"].astype(str)

    # Create figure
    fig = go.Figure()

    # Bar plot for daily count
    fig.add_trace(
        go.Bar(
            x=date_counts["Date"],
            y=date_counts["Count"],
            name="Daily Entries",
            marker_color="#1f77b4",
            opacity=0.6,
        )
    )

    # Scatter plot for cumulative count
    fig.add_trace(
        go.Scatter(
            x=date_counts["Date"],
            y=date_counts["Cumulative_Count"],
            name="Cumulative Entries",
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=2),
            marker=dict(size=8),
        )
    )

    # Update layout with more explicit x-axis configuration
    fig.update_layout(
        title="Federal Register Publication Dates",
        xaxis_title="Date",
        yaxis_title="Entries",
        legend_title_text="Metrics",
        xaxis=dict(
            tickmode='array',
            tickvals=date_counts["Date"],
            ticktext=date_counts["Date"]
        )
    )

    return pltoff.plot(fig, output_type="div", include_plotlyjs="cdn")

def generate_html_report(filepath, output_path="index.html"):
    """
    Generate a static HTML report with table and interactive plot.

    Args:
        filepath (str): Path to input JSONL file
        output_path (str): Path to output HTML file
    """
    # Load and process data
    data = load_jsonl_data(filepath)
    df = create_dataframe(data)

    # Generate plot
    fed_reg_plot = generate_fed_reg_date_plot(df)

    # Convert DataFrame to HTML with a unique ID
    table_html = df.to_html(
        classes="table table-striped table-hover", table_id="meetingsTable", index=False
    )

    # HTML Template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Meeting Data Visualization</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.datatables.net/2.0.2/css/dataTables.bootstrap5.min.css" rel="stylesheet">
        <style>
            body {{ padding: 20px; }}
            .plot-container {{ margin-bottom: 30px; }}
            .table-container {{ max-height: 600px; overflow-y: auto; }}
            #meetingsTable {{ width: 100% !important; }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
        <h1 class="text-center mb-4" style="font-size: 2.5rem; color: #4CAF50; font-weight: bold;">NIH Federal Register Closed Meeting Tracker</h1>
        <p class="text-center" style="font-size: 1.2rem; color: #555; line-height: 1.6;">
        This report tracks closed meetings published in the <a href="https://www.federalregister.gov/agencies/national-institutes-of-health" target="_blank" rel="noopener noreferrer" style="color: #007bff; text-decoration: underline;">National Institutes of Health (NIH) Federal Register</a>.
        </p>
        <p class="text-center" style="font-size: 1.1rem; color: #555; font-weight: bold; line-height: 1.6;">
        This report may contain errors. Please verify the details before drawing any conclusions.
        </p>
        <p class="text-center" style="font-size: 1.1rem; color: #555; line-height: 1.6;">
        Created by <a href="https://evoquantbio.com/" target="_blank" rel="noopener noreferrer" style="color: #007bff; text-decoration: underline;">Evoquant Bio</a>.
        </p>
            <div class="row">
                <div class="col-12 plot-container">
                    {fed_reg_plot}
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="table-container">
                        {table_html}
                    </div>
                </div>
            </div>
        </div>

        <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
        <script src="https://cdn.datatables.net/2.0.2/js/dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/2.0.2/js/dataTables.bootstrap5.min.js"></script>
        <script>
            $(document).ready(function() {{
                $('#meetingsTable').DataTable({{
                    pageLength: 25,
                    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                    order: []
                }});
            }});
        </script>
    </body>
    </html>
    """

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_template)

    print(f"Report generated at {output_path}")


# Example usage
generate_html_report("data.json")
