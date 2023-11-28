import streamlit as st
import plotly.express as px
import pandas as pd
import warnings
import  json
from PIL import Image
from pathlib import Path
import streamlit as st
import sqlite3
from streamlit_lottie import st_lottie
from passlib.hash import pbkdf2_sha256 
warnings.filterwarnings('ignore')

# Database setup
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


#  ------------------------------------------- Streamlit App ---------------------------------- #

# ML-implemented Dashboard
def dashboard():
    #----- Load file for Analysis ----------#
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
            fig = px.bar(category_df, x = "Category", y = "Sales", text = ['${:,.2f}'.format(x) for x in category_df["Sales"]],
                        template = "seaborn")
            st.plotly_chart(fig,use_container_width=True, height = 200)

        with col2:
            st.subheader(":chart: :orange[REGION WISE SALES :] ")
            fig = px.pie(filtered_df, values = "Sales", names = "Region", hole = 0.5)
            fig.update_traces(text = filtered_df["Region"], textposition = "outside")
            st.plotly_chart(fig,use_container_width=True)
        
            
        # ======================== View and Download Filtered data ========================= #
        st.subheader(":arrow_down: :orange[VIEW FILTERD DATA] :arrow_down:")
        cl1, cl2 = st.columns((2))
        with cl1:
            with st.expander("Category-Wise Data (:heavy_dollar_sign:)"):
                st.write(category_df.style.background_gradient(cmap="Blues"))
                csv = category_df.to_csv(index = False).encode('utf-8')
                st.download_button("Download Data", data = csv, file_name = "Category.csv", mime = "text/csv",
                                    help = 'Click here to download the data as a CSV file')

        with cl2:
            with st.expander("Region-Wise Data (:heavy_dollar_sign:)"):
                region = filtered_df.groupby(by = "Region", as_index = False)["Sales"].sum()
                st.write(region.style.background_gradient(cmap="Oranges"))
                csv = region.to_csv(index = False).encode('utf-8')
                st.download_button("Download Data", data = csv, file_name = "Region.csv", mime = "text/csv",
                                help = 'Click here to download the data as a CSV file')
            
                
        # ======================= Apply Time Series Analysis on the Given dataset ================================== #
        filtered_df["Month_Year"] = filtered_df["Order Date"].dt.to_period("M")
        st.subheader(':chart_with_upwards_trend: :orange[SALES - DATA ANALYSIS BASED ON TIME SERIES :] :arrow_down_small:')

        linechart = pd.DataFrame(filtered_df.groupby(filtered_df["Month_Year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
        fig2 = px.line(linechart, x = "Month_Year", y="Sales", labels = {"Sales": "Amount"},height=500, width = 1000,template="gridon")
        st.plotly_chart(fig2,use_container_width=True)

        with st.expander("View TimeSeries Data (:spiral_calendar_pad:):"):
            st.write(linechart.T.style.background_gradient(cmap="Blues"))
            csv = linechart.to_csv(index=False).encode("utf-8")
            st.download_button('Download Data', data = csv, file_name = "TimeSeries.csv", mime ='text/csv')
            
        # ======================= Tree Map Based On Region, Category and Sub-Category ========================================== #
        st.subheader(":abacus: :orange[Hierarchical view of Sales using Tree-Map :] ")
        fig3 = px.treemap(filtered_df, path = ["Region","Category","Sub-Category"], values = "Sales",hover_data = ["Sales"],
                        color = "Sub-Category")
        fig3.update_layout(width = 800, height = 650)
        st.plotly_chart(fig3, use_container_width=True)

        # ============================= Segment and Category Wise Sales Pie Chart ===================================== #
        chart1, chart2 = st.columns((2))
        with chart1:
            st.subheader(':arrow_double_down: :orange[SEGMENT WISE SALES] :arrow_double_down:')
            fig = px.pie(filtered_df, values = "Sales", names = "Segment", template = "plotly_dark")
            fig.update_traces(text = filtered_df["Segment"], textposition = "inside")
            st.plotly_chart(fig,use_container_width=True)

        with chart2:
            st.subheader(':arrow_double_down: :orange[CATEGORY WISE SALES] :arrow_double_down:')
            fig = px.pie(filtered_df, values = "Sales", names = "Category", template = "gridon")
            fig.update_traces(text = filtered_df["Category"], textposition = "inside")
            st.plotly_chart(fig,use_container_width=True)

        # ================================ Month wise Sales Analysis Table ============================= #
        import plotly.figure_factory as ff
        #Top 5 sales summary
        st.subheader(":moneybag: :orange[TOP 5 SALES DATA SUMMARY :] ")
        with st.expander(":page_with_curl: Summary_Table (Top 5 Sales) :"):
            df_sample = df[0:5][["Region","State","City","Category","Sales","Profit","Quantity"]]
            fig = ff.create_table(df_sample, colorscale = "Cividis")
            st.plotly_chart(fig, use_container_width=True)
        # Month wise Sub-Category sales summary    
        st.subheader(":black_square_for_stop: :orange[MONTH WISE SUB-CATEGORY SALES DATA :] ")
        with st.expander(":page_facing_up: Month wise sub-Category Table :"):
            filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
            sub_category_Year = pd.pivot_table(data = filtered_df, values = "Sales", index = ["Sub-Category"],columns = "month")
            st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

        # =============================== Scatter Plot for realtion between Sales and Profit ========================================== # 
        st.subheader(":currency_exchange: :orange[Relationship between Sales(:heavy_dollar_sign:) and Profits(:heavy_dollar_sign:) using Scatter Plot. :] ")
        data1 = px.scatter(filtered_df, x = "Sales", y = "Profit", size = "Quantity")
        data1['layout'].update(title="",
                            titlefont = dict(size=20),xaxis = dict(title="Sales",titlefont=dict(size=19)),
                            yaxis = dict(title = "Profit", titlefont = dict(size=19)))
        st.plotly_chart(data1,use_container_width=True)

        # ============================ VIEW AND DOWNLOAD FULL DATASET ======================================== #
        st.subheader(":memo: :orange[COMPLETE DATASET :]")
        #view
        with st.expander("View Data :point_down:"):
            st.write(filtered_df.style.background_gradient(cmap="Oranges"))

        #Downlod
        csv = df.to_csv(index = False).encode('utf-8')
        st.download_button('Download Data', data = csv, file_name = "Dataset.csv",mime = "text/csv")

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

# Main Home Page Function
def main():
    
    # Page Setup
    st.set_page_config(page_title="Smart-Sales", page_icon=":bar_chart:", layout="wide")
    st.title(" :bar_chart: :orange[-- * SMART-SALES * --] :bar_chart:")   
    st.subheader(":money_with_wings: :violet[Where Data Meets Destiny] :money_with_wings:")
    image = Image.open(r"C:\Users\MAYANK JHA\OneDrive\Desktop\Final Year Project\smart sales logos.jpeg")
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
