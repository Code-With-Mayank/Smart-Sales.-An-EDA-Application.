import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
import warnings
import json
from PIL import Image
from pathlib import Path
import sqlite3
from streamlit_lottie import st_lottie
from passlib.hash import pbkdf2_sha256 
from sklearn.cluster import KMeans
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.linear_model import LinearRegression
import numpy as np
import pdfkit
import os
from tempfile import TemporaryDirectory
from jinja2 import Template
import base64
import urllib.parse

warnings.filterwarnings('ignore')

# Pdfkit path configuration
# Update the path to use the local wkhtmltopdf executable
path_to_wkhtmltopdf = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bin', 'wkhtmltopdf.exe'))

# Debug information
print(f'Path to wkhtmltopdf: {path_to_wkhtmltopdf}')
print(f'File exists: {os.path.isfile(path_to_wkhtmltopdf)}')

config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

#Database setup
conn = sqlite3.connect('user.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
''')
conn.commit()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# ------------- Animations ----------
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return  json.load(f)
    
def fig_to_base64(fig):
    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64
    

# Function to generate PDF report
def generate_pdf(html_content, filename='Report.pdf'):
    options = {
        'enable-local-file-access': None,
        'no-stop-slow-scripts': None
    }
    pdfkit.from_string(html_content, filename, configuration=config, options=options)
 
# Function to save Plotly figures as images
def save_fig_as_image(fig, filename):
    fig.write_image(filename)

# Function to generate HTML content for the PDF report
def create_report_html(image_paths):
    html_content = f"""
    <html>
    <head>
        <title>Sales Analysis Report</title>
    </head>
    <body>
    <h1>Sales Analysis Report</h1>
    <h2>Figures</h2>
    """
    for img_path in image_paths:
        html_content += f'<img src="file:///{img_path}" style="width:100%; height:auto;"><br>'
    html_content += "</body></html>"
    return html_content


#  --------------------------------------------------- MAIN STREAMLIT APP ---------------------------------------------------- #

# ML-implemented Dashboard
def dashboard():
    #----- Load file for Analysis ----------#
    st.header(":house: DASHBOARD :house:")
    fl = st.file_uploader(":file_folder: Upload a file",type=(["csv","txt","xlsx","xls"]))
    if fl is None:
        lottie_hello1 = load_lottiefile("lottiefiles/Home-Main.json")
        st_lottie(
                lottie_hello1,
                speed = 1,
                reverse=False,
                loop=True,
                quality="high",
                height =500,
                width=500,
                key=None,
            )
    elif fl is not None:
        filename = fl.name
        st.write(filename)
        df = pd.read_csv(filename, encoding = "ISO-8859-1")
        
        # ========================= For Time Series Analysis, Getting Date ============================== #   
        col1, col2 = st.columns((2))
        df["Order Date"] = pd.to_datetime(df["Order Date"])

        # Getting the start and end date 
        startDate = pd.to_datetime(df["Order Date"]).min()
        endDate = pd.to_datetime(df["Order Date"]).max()

        with col1:
            date1 = pd.to_datetime(st.date_input(":spiral_calendar_pad: :orange[START DATE] :", startDate))

        with col2:
            date2 = pd.to_datetime(st.date_input(":spiral_calendar_pad: :orange[END DATE] :", endDate))

        df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

        # =========================== Apply Filters in the Dataset =========================================== #  
        st.sidebar.header("Choose your filter: ")
        st.markdown(
         f'''
              <style>
                 .sidebar .sidebar-content {{
                 width: 375px;
                    }}
                </style>
            ''',
            unsafe_allow_html=True
        )
        # Create Filter based on Region
        region = st.sidebar.multiselect("Select Region: ", df["Region"].unique())
        if not region:
            df2 = df.copy()
        else:
            df2 = df[df["Region"].isin(region)]

        # Create Filter based on State
        state = st.sidebar.multiselect("Select the States :", df2["State"].unique())
        if not state:
            df3 = df2.copy()
        else:
            df3 = df2[df2["State"].isin(state)]

        # Create Filter based on City
        city = st.sidebar.multiselect("Select the Cities :",df3["City"].unique())

        # Filter the given Data
        if not region and not state and not city:
            filtered_df = df
        elif not state and not city:
            filtered_df = df[df["Region"].isin(region)]
        elif not region and not city:
            filtered_df = df[df["State"].isin(state)]
        elif state and city:
            filtered_df = df3[df["State"].isin(state) & df3["City"].isin(city)]
        elif region and city:
            filtered_df = df3[df["Region"].isin(region) & df3["City"].isin(city)]
        elif region and state:
            filtered_df = df3[df["Region"].isin(region) & df3["State"].isin(state)]
        elif city:
            filtered_df = df3[df3["City"].isin(city)]
        else:
            filtered_df = df3[df3["Region"].isin(region) & df3["State"].isin(state) & df3["City"].isin(city)]

        # ========================= Plotting of the bars and Charts ====================================================== #
        category_df = filtered_df.groupby(by = ["Category"], as_index = False)["Sales"].sum()

        with col1:
            st.subheader(":chart: :orange[CATEGORY WISE SALES :] ")
            fig13 = px.bar(category_df, x = "Category", y = "Sales", text = ['${:,.2f}'.format(x) for x in category_df["Sales"]],
                    template = "seaborn")
            st.plotly_chart(fig13,use_container_width=True, height = 200)

        with col2:
            st.subheader(":chart: :orange[REGION WISE SALES :] ")
            fig14 = px.pie(filtered_df, values = "Sales", names = "Region", hole = 0.5)
            fig14.update_traces(text = filtered_df["Region"], textposition = "outside")
            st.plotly_chart(fig14,use_container_width=True)
        
        # ======================== View and Download Filtered data ========================= #
        st.subheader(":arrow_down: :orange[VIEW FILTERED DATA] :arrow_down:")
        cl1, cl2 = st.columns((2))
        with cl1:
            with st.expander("Category-Wise Data (:heavy_dollar_sign:)"):
                st.write(category_df.style.background_gradient(cmap="Blues"))
                csv = category_df.to_csv(index = False).encode('utf-8')
                st.download_button("Download Data:inbox_tray:", data = csv, file_name = "Category.csv", mime = "text/csv",
                                    help = 'Click here to download the data as a CSV file')

        with cl2:
            with st.expander("Region-Wise Data (:heavy_dollar_sign:)"):
                region = filtered_df.groupby(by = "Region", as_index = False)["Sales"].sum()
                st.write(region.style.background_gradient(cmap="Oranges"))
                csv = region.to_csv(index = False).encode('utf-8')
                st.download_button("Download Data:inbox_tray:", data = csv, file_name = "Region.csv", mime = "text/csv",
                                help = 'Click here to download the data as a CSV file')
                
        # ================================ Segment and Category Wise Sales Pie Chart ===================================== #
        chart1, chart2 = st.columns((2))
        with chart1:
            st.subheader(':arrow_double_down: :orange[SEGMENT WISE SALES] :arrow_double_down:')
            fig1 = px.pie(filtered_df, values = "Sales", names = "Segment", template = "plotly_dark")
            fig1.update_traces(text = filtered_df["Segment"], textposition = "inside")
            st.plotly_chart(fig1,use_container_width=True)

        with chart2:
            st.subheader(':arrow_double_down: :orange[SUB-CATEGORY WISE SALES] :arrow_double_down:')
            fig2 = px.pie(filtered_df, values = "Sales", names = "Sub-Category", template = "gridon")
            fig2.update_traces(text = filtered_df["Sub-Category"], textposition = "inside")
            st.plotly_chart(fig2,use_container_width=True)

        # ================================ Month wise Sales Analysis Table ============================= #
        # Top 5 sales summary
        st.subheader(":trophy: :orange[TOP 5 SALES DATA SUMMARY :] ")
        with st.expander(":page_with_curl: Summary_Table (Top 5 Sales) :"):
            df_sample = df[0:5][["Region","State","City","Category","Sales","Profit","Quantity"]]
            fig3 = ff.create_table(df_sample, colorscale = "Cividis")
            st.plotly_chart(fig3, use_container_width=True)
        # Month wise Sub-Category sales summary    
        st.subheader(":black_square_for_stop: :orange[MONTH WISE SUB-CATEGORY SALES DATA :] ")
        with st.expander(":page_facing_up: Month wise sub-Category Table :"):
            filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
            sub_category_Year = pd.pivot_table(data = filtered_df, values = "Sales", index = ["Sub-Category"],columns = "month")
            st.write(sub_category_Year.style.background_gradient(cmap="Blues"))
            
        # ======================= Applying Time Series Analysis on the Given dataset ================================== #
        filtered_df["Month_Year"] = filtered_df["Order Date"].dt.to_period("M")
        st.subheader(':hourglass_flowing_sand: :orange[SALES - DATA ANALYSIS BASED ON TIME SERIES :] :hourglass_flowing_sand:')

        linechart = pd.DataFrame(filtered_df.groupby(filtered_df["Month_Year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
        fig4 = px.line(linechart, x = "Month_Year", y="Sales", labels = {"Sales": "Amount"},height=500, width = 1000,template="gridon")
        st.plotly_chart(fig4,use_container_width=True)

        with st.expander("View TimeSeries Data (:spiral_calendar_pad:):"):
            st.write(linechart.T.style.background_gradient(cmap="Blues"))
            csv = linechart.to_csv(index=False).encode("utf-8")
            st.download_button('Download Data:inbox_tray:', data = csv, file_name = "TimeSeries.csv", mime ='text/csv')
            
        # ======================= Tree Map Based On Region, Category and Sub-Category ========================================== #
        st.subheader(":abacus: :orange[HIERARCHICAL VIEW OF SALES USING TREE MAP :] ")
        fig5 = px.treemap(filtered_df, path = ["Region","Category","Sub-Category"], values = "Sales",hover_data = ["Sales"],
                        color = "Sub-Category")
        fig5.update_layout(width = 800, height = 650)
        st.plotly_chart(fig5, use_container_width=True)
        
        # ===================== Box Plot for Sales Distribution by Category ======================== #
        st.subheader(":package: :orange[BOX PLOT FOR SALES:]")
        fig7 = px.box(filtered_df, x="Sub-Category", y="Sales", points="all")
        st.plotly_chart(fig7, use_container_width=True)
        
        # ===================== Bubble Chart for Sales and Profit ============================== #
        st.subheader(":crystal_ball: :orange[BUBBLE CHART FOR SALES AND PROFIT BY REGION:]")
        fig6 = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity", color="Region", hover_name="City",
                                size_max=60)
        st.plotly_chart(fig6, use_container_width=True)
        
        # ====================================== Sales and Profit Distribution plots =========================== #

        st.subheader(":moneybag: :orange[DISTRIBUTION OF SALES AND PROFIT] :moneybag:")

        # Create columns for plots
        dist_col1, dist_col2 = st.columns(2)

        # Violin Plot for Sales Distribution
        with dist_col1:
            fig8 = px.violin(filtered_df, y="Sales", box=True, points="all",
                                        title="Sales Distribution", template="plotly_dark")
            st.plotly_chart(fig8, use_container_width=True)

        # Violin Plot for Profit Distribution
        with dist_col2:
            fig9 = px.violin(filtered_df, y="Profit", box=True, points="all",
                                        title="Profit Distribution", template="plotly_dark")
            st.plotly_chart(fig9, use_container_width=True)

        # Scatter plot with marginal histograms to show the relationship between Sales and Profit
        st.subheader(":chart_with_upwards_trend: :orange[Sales vs. Profit Distribution] :chart_with_upwards_trend:")
        fig10 = px.scatter(filtered_df, x="Sales", y="Profit", color="Region",
                                        marginal_x="histogram", marginal_y="histogram",
                                        title="Sales vs. Profit with Marginal Histograms", template="plotly_dark")
        st.plotly_chart(fig10, use_container_width=True)

       # =============================== Scatter Plot for realtion between Sales and Profit using KMeans  Clustering  ========================================== # 
        st.subheader(":currency_exchange: :orange[RELATIONSHIP BETWEEN SALES(:heavy_dollar_sign:) AND PROFITS(:heavy_dollar_sign:) USING SCATTER PLOT(:gear:)] ")
        kmeans = KMeans(n_clusters=3)
        filtered_df['Cluster'] = kmeans.fit_predict(filtered_df[['Sales', 'Profit', 'Quantity']])
        fig11 = px.scatter(filtered_df, x="Sales", y="Profit", color="Cluster", hover_name="City", size="Quantity")
        st.plotly_chart(fig11, use_container_width=True)
        
      # =========================== Sales Forecasting and Prediction using Linear Regression =========================================== #
        st.subheader(" :chart_with_upwards_trend: :orange[SALES FORECASTING BETWEEN ACTUAL AND PREDICTED SALES:]:chart_with_downwards_trend:")

        # Prepare the data for linear regression
        filtered_df['Order Date'] = pd.to_datetime(filtered_df['Order Date'])
        filtered_df['Days'] = (filtered_df['Order Date'] - filtered_df['Order Date'].min()).dt.days
        X = filtered_df[['Days']]
        y = filtered_df['Sales']

        # Fit the model
        model = LinearRegression()
        model.fit(X, y)

        # Make predictions
        filtered_df['Predicted_Sales'] = model.predict(X)

        # Generate dates for the forecast
        future_days = pd.date_range(filtered_df['Order Date'].max(), periods=30, freq='D')
        future_days_df = pd.DataFrame((future_days - filtered_df['Order Date'].min()).days, columns=['Days'])

        # Predict future sales
        future_predictions = model.predict(future_days_df)

        # Prepare data for plotting
        forecast_df = pd.DataFrame({
            'Date': pd.concat([filtered_df['Order Date'], pd.Series(future_days)]).reset_index(drop=True),
            'Sales': pd.concat([filtered_df['Sales'], pd.Series([None]*len(future_days))]).reset_index(drop=True),
            'Predicted_Sales': pd.concat([filtered_df['Predicted_Sales'], pd.Series(future_predictions)]).reset_index(drop=True)
        })

        # Create the plot
        fig12 = go.Figure()

        # Add actual sales
        fig12.add_scatter(x=forecast_df['Date'], y=forecast_df['Sales'], mode='lines', name='Actual Sales')

        # Add predicted sales
        fig12.add_scatter(x=forecast_df['Date'], y=forecast_df['Predicted_Sales'], mode='lines', name='Predicted Sales', line=dict(dash='dash'))

        # Add a confidence interval 
        lower_bound = forecast_df['Predicted_Sales'] - np.std(y) / 2
        upper_bound = forecast_df['Predicted_Sales'] + np.std(y) / 2
        fig12.add_scatter(x=forecast_df['Date'], y=lower_bound, fill=None, mode='lines', line_color='lightgrey', showlegend=False)
        fig12.add_scatter(x=forecast_df['Date'], y=upper_bound, fill='tonexty', mode='lines', line_color='lightgrey', showlegend=False, name='Confidence Interval')

        fig12.update_layout(
            title='Sales Forecasting',
            xaxis_title='Date',
            yaxis_title='Sales',
            template='plotly_white',
            legend=dict(x=0, y=1)
        )

        st.plotly_chart(fig12, use_container_width=True)
        
        # ============================ AREAS NEEDING IMPROVEMENT ======================================== #
        st.subheader(":mag: :orange[AREAS NEEDING IMPROVEMENT] :mag:")

        # Average sales calculations
        avg_sales_category = category_df["Sales"].mean()
        avg_sales_region = filtered_df.groupby("Region")["Sales"].sum().mean()
        avg_sales_segment = filtered_df.groupby("Segment")["Sales"].sum().mean()
        
        # Finding areas needing improvement 
        categories_below_avg = category_df[category_df["Sales"] < avg_sales_category]
        sub_categories_df = filtered_df.groupby("Sub-Category")["Sales"].sum().reset_index()
        sub_categories_below_avg = sub_categories_df[sub_categories_df["Sales"] < sub_categories_df["Sales"].mean()]
        regions_df = filtered_df.groupby("Region")["Sales"].sum().reset_index()
        regions_below_avg = regions_df[regions_df["Sales"] < avg_sales_region]
        segment_df = filtered_df.groupby("Segment")["Sales"].sum().reset_index()
        segment_below_avg = segment_df[segment_df["Sales"] < avg_sales_segment]

        # Showing in form of table
        col1, col2 = st.columns((2))
        
        with col1:
            st.subheader(":clipboard: Categories/Sub-Categories Needing Improvement")
            st.write("Categories below average sales:")
            st.write(categories_below_avg.style.background_gradient(cmap="Reds"))
            st.write("Sub-Categories below average sales:")
            st.write(sub_categories_below_avg.style.background_gradient(cmap="Reds"))

        with col2:
            st.subheader(":clipboard: Regions/Segements Needing Improvement")
            st.write("Regions below average sales:")
            st.write(regions_below_avg.style.background_gradient(cmap="Reds"))
            st.write("Segments below average sales:")
            st.write(segment_below_avg.style.background_gradient(cmap="Reds"))
         
     # =============================== Generate PDF Report =============================== #
        st.subheader(":page_with_curl: :orange[GENERATE FULL ANALYTICS REPORT] :page_with_curl:")
        if st.button("Generate Report"):
            with TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir).absolute()
                image_paths = []

                # Save figures as images
                fig_paths = {
                    "category_sales.png": fig13,
                    "region_sales.png": fig14,
                    "segment_sales.png": fig1,
                    "sub_category_sales.png": fig2,
                    "top_5_sales.png": fig3,
                    "time_series_analysis.png": fig4,
                    "tree_map.png": fig5,
                    "bubble_chart.png": fig6,
                    "box_plot.png": fig7,
                    "Sales_distribution.png": fig8,
                    "Profit_distributionPro.png": fig9,
                    "Relationship_between_sales_and_profit.png": fig10,
                    "Scatter_plot.png": fig11,
                    "Sales_forecasting.png": fig12,
                    }

                for filename, fig in fig_paths.items():
                    save_path = base_path / filename
                    save_fig_as_image(fig, str(save_path))
                    image_paths.append(save_path)

                # Generate HTML content
                html_content = create_report_html(image_paths,)
                
                # Save HTML to a temporary file
                html_file = base_path / "report.html"
                with open(html_file, "w") as f:
                    f.write(html_content)
                
                # Generate PDF from HTML file
                pdf_path = base_path / "Report.pdf"
                pdfkit.from_file(str(html_file), str(pdf_path), configuration=config, options={'enable-local-file-access': None})

                # Read PDF and provide it for download
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()

                st.download_button(label="Download Report:inbox_tray:", data=pdf_data, file_name="Sales_Report.pdf", mime="application/pdf")


     # ============================ VIEW AND DOWNLOAD FULL DATASET ======================================== #
        st.subheader(":memo: :orange[COMPLETE DATASET :]")
        #view
        with st.expander("View Data :point_down:"):
            st.write(filtered_df.style.background_gradient(cmap="Oranges"))

        #Download
        csv = df.to_csv(index = False).encode('utf-8')
        st.download_button('Download Data:inbox_tray:', data = csv, file_name = "Dataset.csv",mime = "text/csv")
                
#Login function
def login():
    st.info("If you do not have an account. Go to Signup Option in the Menu to Create One.")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Logged in Succesfully. Click Again to Explore.")
        else:
            st.warning("Incorrect username or password")

#Logout Function
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("You have been logged out. Click Again to go to Main Menu")

#Signup Function
def sign_up():
    new_username = st.text_input("Create a username")
    new_password = st.text_input("Create a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")
    if st.button("Sign Up"):
        if new_password == confirm_password:
            hashed_password = hash_password(new_password)
            add_user(new_username, hashed_password)
            st.success("Account created successfully. You can now log in.")
        else:
            st.warning("Passwords do not match")

#Hash Password
def hash_password(password):
    return pbkdf2_sha256.hash(password)

#Verify User
def verify_user(username, password):
    cursor.execute('SELECT password FROM users WHERE username=?', (username,))
    result = cursor.fetchone()
    if result:
        return pbkdf2_sha256.verify(password, result[0])
    return False

#Add user to Database
def add_user(username, password):
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

#Main Function
def main():
    # Page Setup
    st.set_page_config(page_title="Smart-Sales", page_icon=":bar_chart:", layout="wide")
    st.title(" :bar_chart: :orange[-- * SMART-SALES * --] :bar_chart:")   
    st.subheader(":money_with_wings: :violet[Where Data Meets Destiny] :money_with_wings:")
    image = Image.open("images/smart_sales_ logo.jpeg")
    st.sidebar.image(image, caption='ANALYZE - VISUALIZE - GENERATE',use_column_width="always")    
    st.markdown('<style>div.block-container{padding-top:0 rem;}</style>',unsafe_allow_html=True)
    

    #----- PATH SETINGS ----------------#
    current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    css_file = current_dir / "main.css"

    with open(css_file) as f:
        st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

    if st.session_state.logged_in:
        st.sidebar.subheader(f":red[Welcome !! , {st.session_state.username}😊]")
        st.markdown(
         f'''
              <style>
                 .sidebar .sidebar-content {{
                 width: 375px;
                    }}
                </style>
            ''',
            unsafe_allow_html=True
        )
        # Main Application Function
        dashboard()
        # Logout button
        if st.sidebar.button("Logout"):
            logout()
    else:
        menu = ["Home","Login", "Sign Up"]
        choice = st.sidebar.selectbox("**:red[MENU ⚙️]**", menu)
        lottie_hello = load_lottiefile("lottiefiles/Home-Sidebar.json")
        with st.sidebar:
            st_lottie(
                lottie_hello,
                speed = 1,
                reverse=False,
                loop=True,
                quality="high",
                height =200,
                width=350,
                key=None,
            )
        st.markdown(
         f'''
              <style>
                 .sidebar .sidebar-content {{
                 width: 375px;
                    }}
                </style>
            ''',
            unsafe_allow_html=True
        )
        if choice == "Home":
            st.subheader(":red[Welcome to SMART-SALES - Your Gateway to Exploratory Sales Data !!💹]")
            home1 = '''
            Where innovation meets exploration in the world of sales data! 
            Our cutting-edge Exploratory Sales Data Application is designed to revolutionize the way you analyze, understand, and leverage your sales data. 
            Whether you're a seasoned sales professional or just starting your journey, 
            SMART-SALES empowers you with the tools you need to make informed decisions and drive unprecedented success.'''
            st.markdown(home1)
            st.subheader(":green[👇Key Features👇]")
            home2 = '''
            **:green[1. Intuitive Dashboard:]**
            Our user-friendly dashboard provides a real-time snapshot of your sales performance. 
            Visualize key metrics, track trends, and gain insights at a glance. 
            SMART-SALES ensures you are always in control, allowing you to make data-driven decisions effortlessly.

            **:green[2. Dynamic Data Exploration:]**
            Dive deep into your sales data with our powerful exploration tools. 
            Uncover hidden patterns, identify opportunities, and understand customer behavior like never before. 
            SMART-SALES puts the power of data exploration at your fingertips.

            **:green[3. Predictive Analytics:]**
            Stay ahead of the curve with our advanced predictive analytics. 
            Anticipate market trends, forecast sales, and optimize your strategies for maximum impact.
            SMART-SALES doesn't just show you where you've been; it guides you to where you want to go.
            '''
            col1, col2= st.columns(2, gap="small")
            with col1:
                st.markdown(home2)
            with col2:
                lottie_hi = load_lottiefile("lottiefiles/Home-Mid.json")
                st_lottie(
                lottie_hi,
                speed = 1,
                reverse=False,
                loop=True,
                quality="high",
                height =500,
                width=400,
                key=None,
            )
            st.subheader(":blue[⚡ Get Started Today !⚡]")
            st.markdown("**:orange[Are you ready to revolutionize your approach to sales data?]**")
            home3 = ''' 
            Join the SMART-SALES community and embark on a journey of exploration, innovation, and unparalleled success. 
            Sign up / Login From the Menu to experience the future of Exploratory Sales Data Applications. 
            '''
            st.markdown(home3)
        elif choice == "Login":
            st.subheader(":red[Login Menu]")
            login()

        elif choice == "Sign Up":
            st.subheader(":red[Create Account]")
            sign_up()


if __name__ == '__main__':
    main()
