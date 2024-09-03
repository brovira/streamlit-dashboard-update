import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# Load data function using the updated caching mechanism
@st.cache_data
def load_data():
    reviews = pd.read_csv('reviews_Q1.csv')
    bookings = pd.read_csv('2024_Q1.csv')

    # Select only the necessary columns from the reviews DataFrame
    reviews_subset = reviews[['code', 'rating', 'value_rating', 'communication_rating', 'location_rating', 'cleanliness_rating', 'accuracy_rating', 'checkin_rating']]

    # Merge df with the selected columns from reviews using a left join
    df = pd.merge(bookings, reviews_subset, on='code', how='left')

    df['checkin_date'] = pd.to_datetime(df['checkin_date'])
    df['checkout_date'] = pd.to_datetime(df['checkout_date'])
    df['month'] = df['checkin_date'].dt.to_period('M').dt.start_time  # Convert to the first day of the month

    # Calculate nightly rate if not already present
    df['nightly_rate'] = df['revenue'] / df['nights']
    return df

# KPI Calculations
def calculate_kpis(df):
    total_nights = df['nights'].sum()
    total_revenue = df['revenue'].sum()
    
    # Calculate the total available nights based on the data provided
    num_properties = len(df['property_name'].unique())
    period_days = (df['checkout_date'].max() - df['checkin_date'].min()).days + 1
    total_available_nights = period_days * num_properties
    
    occupancy_rate = round((total_nights / total_available_nights) * 100, 2)
    adr = round((total_revenue / total_nights), 2) if total_nights else 0
    revpar = round((total_revenue / total_available_nights), 2) if total_available_nights else 0

    # Ensure booking_date is converted to datetime format
    df['booking_date'] = pd.to_datetime(df['booking_date'])
    df['lead_time'] = round((df['checkin_date'] - df['booking_date']), 2)
    # Correct the lead_time calculation if necessary
    if 'lead_time' not in df.columns or df['lead_time'].dtype != 'int64':
        df['lead_time'] = (df['checkin_date'] - df['booking_date']).dt.days  # Assuming these columns exist

    # Calculate average lead time in days
    lead_time = round((df['checkin_date'] - df['booking_date']).dt.days.mean(), 2)

    # Calculate the number of reservations
    number_of_reservations = df.shape[0]

    # Calculate the average length of stay
    average_length_of_stay = round(df['nights'].mean(), 2)

    # Calculate averages for rating KPIs
    average_rating = round(df['rating'].mean(), 2) if 'rating' in df.columns else 0
    value_rating = round(df['value_rating'].mean(), 2) if 'value_rating' in df.columns else 0
    communication_rating = round(df['communication_rating'].mean(), 2) if 'communication_rating' in df.columns else 0
    location_rating = round(df['location_rating'].mean(), 2) if 'location_rating' in df.columns else 0
    cleanliness_rating = round(df['cleanliness_rating'].mean(), 2) if 'cleanliness_rating' in df.columns else 0
    accuracy_rating = round(df['accuracy_rating'].mean(), 2) if 'accuracy_rating' in df.columns else 0
    checkin_rating = round(df['checkin_rating'].mean(), 2) if 'checkin_rating' in df.columns else 0

    return {
        'Total Revenue': f"{total_revenue:,.2f}€",
        'Occupancy Rate (%)': f"{occupancy_rate}%",
        'Average Daily Rate (ADR)': f"{adr}€",
        'Revenue Per Available Room (RevPAR)': f"{revpar}€",
        'Average Lead Time (days)': f"{lead_time}",
        'Average Length of Stay (nights)': average_length_of_stay,
        'Number of Reservations': number_of_reservations,
        'Average Rating': average_rating,
        'Value Rating': value_rating,
        'Communication Rating': communication_rating,
        'Location Rating': location_rating,
        'Cleanliness Rating': cleanliness_rating,
        'Accuracy Rating': accuracy_rating,
        'Check-in Rating': checkin_rating
    }

def plot_revenue_per_platform(df):
    revenue_per_platform = df.groupby('platform')['revenue'].sum().reset_index()
    fig = px.bar(revenue_per_platform, x='platform', y='revenue', title='Revenue per Platform',
                 color='platform', color_discrete_map={'airbnb': 'red', 'booking.com': 'blue', 'vrbo': 'purple'})
    return fig

def plot_revenue_percentage_per_platform(df):
    revenue_per_platform = df.groupby('platform')['revenue'].sum().reset_index()
    fig = px.pie(revenue_per_platform, values='revenue', names='platform', title='Percentage of Revenue per Platform',
                 color='platform', color_discrete_map={'airbnb': 'red', 'booking.com': 'blue', 'vrbo': 'purple'},
                 hole=0.3)
    return fig

def plot_nights_booked_percentage_per_platform(df):
    # Filter out rows where 'status' is 'cancelled'
    filtered_df = df[df['status'] != 'cancelled']
    
    # Group by 'platform' and sum the 'nights'
    nights_per_platform = filtered_df.groupby('platform')['nights'].sum().reset_index()
    
    # Plot a pie chart
    fig = px.pie(nights_per_platform, values='nights', names='platform',
                 title='Percentage of Nights Booked per Platform',
                 color='platform',
                 color_discrete_map={'airbnb': 'red', 'booking.com': 'blue', 'vrbo': 'purple'},
                 hole=0.3)
    return fig

def plot_stacked_revenue_by_property_platform(df):

    # Group data by property and platform, then sum the revenue
    revenue_per_property_platform = df.groupby(['property_name', 'platform'], observed = True)['revenue'].sum().reset_index()

    # Calculate total revenue per property
    total_revenue_per_property = revenue_per_property_platform.groupby('property_name', observed = True)['revenue'].sum().reset_index()


    # Create a stacked bar chart with Plotly Express
    fig = px.bar(revenue_per_property_platform, x='property_name', y='revenue',
             color='platform',  # This will create the stack effect
             title='Revenue per Property by Platform',
             labels={'revenue': 'Total Revenue', 'property_name': 'Property Name'},
             color_discrete_map={'airbnb': 'red', 'booking.com': 'blue', 'vrbo': 'purple'})

    # Add total revenue text annotations on top of each stacked bar
    for idx, row in total_revenue_per_property.iterrows():
        fig.add_annotation(x=row['property_name'], y=row['revenue'],
                       text=f"Total: {row['revenue']:,.2f}€",
                       showarrow=False, font={'size': 12, 'color': 'white'},
                       yshift=10, xshift=0)

    # Improve layout and customization if necessary
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})

    # Show the plot
    return fig

# Main function where we define the app
def main():
    df = load_data()

    # Streamlit title and introduction
    st.title("BI Dashboard for Short Term Rental Business")
    st.write("Interactive BI dashboard for analyzing booking data across multiple platforms.")

    # Sidebar - date range filter
    st.sidebar.header("Filters")
    if not df.empty:
        min_date = df['checkin_date'].min()
        max_date = df['checkout_date'].max()
        selected_dates = st.sidebar.date_input("Check-in Date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        selected_dates = [pd.Timestamp(date) for date in selected_dates]
        platform_filter = st.sidebar.multiselect("Platform", df['platform'].unique())
        property_filter = st.sidebar.multiselect("Property", df['property_name'].unique())

        # Filtering data based on selection
        filtered_df = df[(df['checkin_date'] >= selected_dates[0]) & (df['checkin_date'] <= selected_dates[1])]
        if platform_filter:
            filtered_df = filtered_df[filtered_df['platform'].isin(platform_filter)]
        if property_filter:
            filtered_df = filtered_df[filtered_df['property_name'].isin(property_filter)]

        # Display KPIs and progress bars
        kpis = calculate_kpis(filtered_df)
        for kpi, value in kpis.items():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric(label=kpi, value=value)
            with col2:
                if "Rating" in kpi:
                    progress_value = float(value) / 5.0 if isinstance(value, (float, int)) else 0
                    st.progress(progress_value)

        # Existing visualizations
        fig1 = plot_revenue_per_platform(filtered_df)
        st.plotly_chart(fig1)
        fig2 = plot_revenue_percentage_per_platform(filtered_df)
        st.plotly_chart(fig2)
        fig3 = plot_nights_booked_percentage_per_platform(filtered_df)
        st.plotly_chart(fig3)
        fig4 = plot_stacked_revenue_by_property_platform(filtered_df)
        st.plotly_chart(fig4)

    else:
        st.write("No data loaded.")

# Run the app
if __name__ == "__main__":
    main()
