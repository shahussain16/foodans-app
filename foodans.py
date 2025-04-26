import streamlit as st
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from datetime import datetime
import plotly.express as px

# Load data
df = pd.read_csv('D:/foodans/modified_madurai_food_shops.csv')
df = df.dropna()

# Score for ranking
df['Score'] = 0.6 * df['Avg_Rating'] + 0.4 * (df['Total_Order'] / df['Total_Order'].max())

# KNN setup
knn_data = df[['Price', 'Avg_Rating']].copy()
knn_data['Food_Type'] = df['Food_Type'].map({'Veg': 0, 'Non-Veg': 1})
knn = NearestNeighbors(n_neighbors=5).fit(knn_data)

# Debug data (optional, remove for production)
print("Unique Types:", df['Type'].unique())
print("Unique Areas:", df['Area'].unique())

# Real-time intro about Madurai with image
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>Sha’s Foodans 🍔✨</h1>", unsafe_allow_html=True)
current_time = datetime.now().strftime("%I:%M %p, Madurai Time")  # e.g., "03:45 PM, Madurai Time"
st.markdown(f"<p style='text-align: center; color: #555;'>Welcome to Madurai, the city famed for its spicy Jigarthanda, sizzling non-veg biryanis, and mouthwatering street food varieties—let’s hunt, less go! 🥰 | Current Time: {current_time}</p>", unsafe_allow_html=True)

# Load and display Madurai image from local disk with corrected path
image_path = r'D:/foodans/img/Madurai.webp'  # Use raw string for Windows path
try:
    st.image(image_path, caption="Madurai’s Vibrant Food Scene", use_container_width=True)
except FileNotFoundError:
    st.error("Image file not found! Please check the path 'D:/foodans/img/Madurai.webp' and ensure the file exists.")
except Exception as e:
    st.error(f"Error loading image: {str(e)}")

# Section 1: Tell Me About You!
st.markdown("---")
st.markdown("<h2 style='color: #FF1493;'>Tell Me About You! 😊</h2>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("What’s your name?")
    age = st.slider("How old are you?", 1, 100, 18)
    diet_type = st.selectbox("Diet Preference?", ["Both", "Veg", "Non-Veg"])  # New preference option
with col2:
    gender = st.selectbox("What’s your gender?", ["Male", "Female", "Others"])
    area = st.selectbox("Where are you in Madurai?", sorted(df['Area'].unique()))

if st.button("Show Top Foods! 🌟"):
    area_df = df[df['Area'] == area]
    # Filter by diet preference
    if diet_type == "Veg":
        area_df = area_df[area_df['Food_Type'] == "Veg"]
    elif diet_type == "Non-Veg":
        area_df = area_df[area_df['Food_Type'] == "Non-Veg"]
    top_vendors = area_df.groupby('Name')['Score'].mean().sort_values(ascending=False).head(5).index
    st.success(f"Hi {name}! Top 5 vendors in {area} ({diet_type} options):")
    for vendor in top_vendors:
        vendor_df = area_df[area_df['Name'] == vendor].sort_values('Score', ascending=False).head(3)
        st.write(f"**{vendor}**")
        for i, row in vendor_df.iterrows():
            st.write(f"- {row['Item_Name']}, ₹{row['Price']}, ⭐ {row['Avg_Rating']}")
        st.button("Order Now! 🍽️", key=f"order_{vendor}", disabled=True)

# Section 2: What’s Your Vibe?
st.markdown("---")
st.markdown("<h2 style='color: #FF1493;'>What’s Your Vibe? 🍽️</h2>", unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    category = st.selectbox(f"{name}, what type?", sorted(df['Type'].unique()))
    price_range = st.selectbox(f"{name}, how much?", ["0-50", "51-100", "101-150", "151+", "Any Price"])
with col4:
    rating_options = ["3.0-3.5", "3.5-4.0", "4.0-4.5", "4.5 and above"]
    min_rating_range = st.selectbox(f"{name}, what rating?", rating_options)
    
    # Dynamic area options based on category
    if category:
        areas_with_category = sorted(df[df['Type'] == category]['Area'].unique())
        if len(areas_with_category) > 0:
            new_area = st.selectbox(f"{name}, same area or new?", ["Same"] + areas_with_category)
        else:
            new_area = st.selectbox(f"{name}, same area or new?", ["Same"] + sorted(df['Area'].unique()))  # Fallback if no areas have the category
    else:
        new_area = st.selectbox(f"{name}, same area or new?", ["Same"] + sorted(df['Area'].unique()))

if st.button("Find My Food! 😋"):
    if price_range == "Any Price":
        price_min, price_max = 0, float('inf')
    else:
        price_min, price_max = map(int, price_range.split('-')) if '-' in price_range else (151, float('inf'))
    search_area = area if new_area == "Same" else new_area
    if min_rating_range == "4.5 and above":
        rating_min = 4.5
        rating_max = float('inf')
    else:
        rating_min, rating_max = map(float, min_rating_range.split('-'))
    filtered = df[(df['Area'] == search_area) & (df['Type'] == category) &  # Strict filter for category
                  (df['Price'].between(price_min, price_max)) & 
                  (df['Avg_Rating'].between(rating_min, rating_max))]
    # Filter by diet preference
    if diet_type == "Veg":
        filtered = filtered[filtered['Food_Type'] == "Veg"]
    elif diet_type == "Non-Veg":
        filtered = filtered[filtered['Food_Type'] == "Non-Veg"]
    
    if filtered.empty:
        st.error(f"Ei {name}, no {category} in {search_area} for {price_range} with {min_rating_range} stars ({diet_type} options)!")
        category_df = df[df['Type'] == category]
        if not category_df.empty:
            # Filter by diet preference
            if diet_type == "Veg":
                category_df = category_df[category_df['Food_Type'] == "Veg"]
            elif diet_type == "Non-Veg":
                category_df = category_df[category_df['Food_Type'] == "Non-Veg"]
            idx = category_df.index[0]
            _, neighbors = knn.kneighbors([knn_data.iloc[idx]])
            similar = df.iloc[neighbors[0]].head(2)
            # Filter similar items by diet preference and category
            if diet_type == "Veg":
                similar = similar[(similar['Food_Type'] == "Veg") & (similar['Type'] == category)]
            elif diet_type == "Non-Veg":
                similar = similar[(similar['Food_Type'] == "Non-Veg") & (similar['Type'] == category)]
            st.write(f"But try these {category} instead:")
            for i, row in similar.iterrows():
                st.write(f"- {row['Item_Name']} at {row['Name']}, ₹{row['Price']}, ⭐ {row['Avg_Rating']}")
    else:
        st.success(f"Wiii {name}! Here’s {category} in {search_area} ({diet_type} options):")
        vendors = filtered['Name'].unique()
        for vendor in vendors:
            vendor_df = filtered[filtered['Name'] == vendor].sort_values('Score', ascending=False).head(4)
            st.write(f"**{vendor}**")
            for i, row in vendor_df.iterrows():
                st.write(f"- {row['Item_Name']}, ₹{row['Price']}, ⭐ {row['Avg_Rating']}")
        st.button("Order Now! 🍽️", key="vibe_order", on_click=lambda: st.write(f"{name}, ordering top {category} item soon!"))
        
        top_item = filtered.sort_values('Score', ascending=False).iloc[0]
        idx = filtered[filtered['Item_Name'] == top_item['Item_Name']].index[0]
        _, neighbors = knn.kneighbors([knn_data.iloc[idx]])
        similar = df.iloc[neighbors[0]].head(3)
        # Filter similar items by diet preference and category
        if diet_type == "Veg":
            similar = similar[(similar['Food_Type'] == "Veg") & (similar['Type'] == category)]
        elif diet_type == "Non-Veg":
            similar = similar[(similar['Food_Type'] == "Non-Veg") & (similar['Type'] == category)]
        st.write(f"{name}, you might like these {category} too:")
        for i, row in similar.iterrows():
            st.write(f"- {row['Item_Name']} at {row['Name']}, ₹{row['Price']}, ⭐ {row['Avg_Rating']}")
        st.button("Order Now! 🍽️", key="similar_vibe_order", on_click=lambda: st.write(f"{name}, ordering top similar {category} item soon!"))

# Section 3: More for You!
if 'top_item' in locals():
    st.markdown("---")
    st.markdown("<h2 style='color: #FF1493;'>More for You! 🌈</h2>", unsafe_allow_html=True)
    # Filter by diet preference
    if diet_type == "Veg":
        top_seller = df[(df['Name'] == top_item['Name']) & (df['Type'] == category) & (df['Food_Type'] == "Veg")].sort_values('Total_Order', ascending=False).iloc[0]
    elif diet_type == "Non-Veg":
        top_seller = df[(df['Name'] == top_item['Name']) & (df['Type'] == category) & (df['Food_Type'] == "Non-Veg")].sort_values('Total_Order', ascending=False).iloc[0]
    else:  # Both
        top_seller = df[(df['Name'] == top_item['Name']) & (df['Type'] == category)].sort_values('Total_Order', ascending=False).iloc[0]
    st.write(f"{name}, top pick from {top_seller['Name']} ({diet_type} options): {top_seller['Item_Name']}, ₹{top_seller['Price']}, ⭐ {top_seller['Avg_Rating']}")
    st.button("Order Now! 🍽️", key="more_order", on_click=lambda: st.write(f"{name}, ordering {top_seller['Item_Name']} soon!"))

# Section 4: What’s Next?
if 'category' in locals():
    st.markdown("---")
    st.markdown("<h2 style='color: #FF1493;'>What’s Next? ⏰</h2>", unsafe_allow_html=True)
    next_types = {
        "Tiffin": ["Tea", "Lunch", "Fast Food"],
        "Fast Food": ["Tea", "Café"],
        "Lunch": ["Café", "Tea", "Fast Food"],
        "Tea": ["Fast Food", "Café","Lunch"],
        "Café": ["Tea", "Tiffin","Lunch"]
    }
    search_area = new_area if 'new_area' in locals() else area if 'area' in locals() else df['Area'].iloc[0]
    if category in next_types:
        st.success(f"Hey {name}, after {category}, how about these in {search_area} ({diet_type} options)?")
        next_options = next_types[category]
        recommendations = []
        for next_type in next_options:
            # Try with search_area first
            next_filtered = df[(df['Type'] == next_type) & (df['Area'] == search_area)].sort_values('Score', ascending=False).head(3)  # Show up to 3 items per type
            # Filter by diet preference
            if diet_type == "Veg":
                next_filtered = next_filtered[next_filtered['Food_Type'] == "Veg"]
            elif diet_type == "Non-Veg":
                next_filtered = next_filtered[next_filtered['Food_Type'] == "Non-Veg"]
            if not next_filtered.empty:
                recommendations.extend(next_filtered.to_dict('records'))  # Add all 3 items if available
            # Fallback to any area if no matches in search_area
            elif not df[df['Type'] == next_type].empty:
                next_fallback = df[df['Type'] == next_type].sort_values('Score', ascending=False).head(3)  # Show up to 3 items
                # Filter by diet preference
                if diet_type == "Veg":
                    next_fallback = next_fallback[next_fallback['Food_Type'] == "Veg"]
                elif diet_type == "Non-Veg":
                    next_fallback = next_fallback[next_fallback['Food_Type'] == "Non-Veg"]
                recommendations.extend(next_fallback.to_dict('records'))
        
        if recommendations:
            unique_recommendations = []  # Avoid duplicates
            seen_items = set()
            for rec in recommendations[:9]:  # Limit to 9 total to ensure 3 unique items max
                if rec['Item_Name'] not in seen_items:
                    unique_recommendations.append(rec)
                    seen_items.add(rec['Item_Name'])
                    if len(unique_recommendations) == 3:  # Stop at 3 unique items
                        break
            for row in unique_recommendations:
                st.write(f"- {row['Item_Name']} ({row['Type']}) at {row['Name']} in {row['Area']}, ₹{row['Price']}, ⭐ {row['Avg_Rating']}")
            st.button("Order Now! 🍽️", key="next_order", on_click=lambda: st.write(f"{name}, ordering top next item soon!"))
        else:
            st.warning(f"No direct matches for {category} in {search_area} ({diet_type} options). Exploring nearby options...")
            category_df = df[df['Type'] == category]
            if not category_df.empty:
                # Filter by diet preference
                if diet_type == "Veg":
                    category_df = category_df[category_df['Food_Type'] == "Veg"]
                elif diet_type == "Non-Veg":
                    category_df = category_df[category_df['Food_Type'] == "Non-Veg"]
                idx = category_df.index[0]
                # Ensure feature names match
                query = knn_data.loc[idx].values.reshape(1, -1)
                _, neighbors = knn.kneighbors(query)
                similar_items = df.iloc[neighbors[0]].head(3)  # Show up to 3 similar items
                # Filter similar items by diet preference and category
                if diet_type == "Veg":
                    similar_items = similar_items[(similar_items['Food_Type'] == "Veg") & (similar_items['Type'] == category)]
                elif diet_type == "Non-Veg":
                    similar_items = similar_items[(similar_items['Food_Type'] == "Non-Veg") & (similar_items['Type'] == category)]
                st.write(f"Try these {category} instead:")
                for i, row in similar_items.iterrows():
                    st.write(f"- {row['Item_Name']} ({row['Type']}) at {row['Name']}, ₹{row['Price']}, ⭐ {row['Avg_Rating']}")
                st.button("Order Now! 🍽️", key="next_similar_order", on_click=lambda: st.write(f"{name}, ordering top similar {category} item soon!"))
            else:
                st.error(f"Oops, {category} isn’t in our data!")

# Section 5: Know Your Vendors!
st.markdown("---")
st.markdown("<h2 style='color: #FF1493;'>Know Your Vendors! 🍴</h2>", unsafe_allow_html=True)

# Area filter for vendors
selected_area = st.selectbox(f"{name}, pick an area to explore vendors!", sorted(df['Area'].unique()))
st.markdown(f"### Vendors in {selected_area} 🌟")
area_df = df[df['Area'] == selected_area]
# Filter by diet preference
if diet_type == "Veg":
    area_df = area_df[area_df['Food_Type'] == "Veg"]
elif diet_type == "Non-Veg":
    area_df = area_df[area_df['Food_Type'] == "Non-Veg"]
if not area_df.empty:
    vendors = area_df['Name'].unique()
    for vendor in vendors:
        vendor_df = area_df[area_df['Name'] == vendor]
        avg_rating = vendor_df['Avg_Rating'].mean()
        total_orders = vendor_df['Total_Order'].sum()
        top_items = vendor_df.sort_values('Total_Order', ascending=False).head(5)  # Changed to top 5
        top_item = top_items.iloc[0]
        st.write(f"🍽️ In {selected_area}, **{vendor}** is a foodie fave with {top_item['Item_Name']} at ₹{top_item['Price']}, ⭐{top_item['Avg_Rating']} ({diet_type} options)!")
        st.write(f"- Avg Rating: {avg_rating:.1f} ⭐ | Total Orders: {total_orders}")
        st.write("Top 5 Dishes:")
        table_data = [{"Item": row[1]['Item_Name'], "Price": f"₹{row[1]['Price']}", "Rating": f"⭐{row[1]['Avg_Rating']}", "Orders": row[1]['Total_Order']} for row in top_items.iterrows()]
        st.table(table_data)
    top_area_items = area_df.sort_values('Total_Order', ascending=False).head(5)
    st.markdown(f"#### {selected_area} Foodie Faves! 🥰")
    st.write(f"It seems {selected_area} people love these foods ({diet_type} options):")
    table_data = [{"Item": row[1]['Item_Name'], "Price": f"₹{row[1]['Price']}", "Rating": f"⭐{row[1]['Avg_Rating']}", "Orders": row[1]['Total_Order']} for row in top_area_items.iterrows()]
    st.table(table_data)

st.markdown("---")
st.markdown(f"### Pick a Vendor to Dive In! 🔍")
vendor = st.selectbox(f"{name}, choose a vendor!", sorted(df['Name'].unique()))  # Show all vendors, no diet filtering
vendor_df = df[df['Name'] == vendor]  # No diet filtering here
if not vendor_df.empty:
    vendor_types = vendor_df['Type'].unique()
    vendor_areas = vendor_df['Area'].unique()
    type_emojis = {"Tiffin": "🥐", "Fast Food": "🍔", "Tea": "🍵", "Café": "☕"}
    emoji = "".join(type_emojis.get(t, "🍽️") for t in vendor_types)
    st.markdown(f"#### {vendor} {emoji}")
    st.write(f"Found in: {', '.join(vendor_areas)}")
    st.write(f"Avg Rating: {vendor_df['Avg_Rating'].mean():.1f} ⭐ | Total Orders: {vendor_df['Total_Order'].sum()}")
    display_df = vendor_df[vendor_df['Type'] == category] if 'category' in locals() and category in vendor_df['Type'].values else vendor_df  # No diet filtering
    top_items = display_df.sort_values('Total_Order', ascending=False).head(7)  # Changed to top 7
    st.write(f"Top Items{' (' + category + ')' if 'category' in locals() else ''}:")
    for i, row in top_items.iterrows():
        with st.expander(f"{row['Item_Name']} ({row['Type']})"):
            st.write(f"Price: ₹{row['Price']} | Rating: ⭐ {row['Avg_Rating']} | Orders: {row['Total_Order']}")
    st.button("Order Now! 🍽️", key="vendor_order", on_click=lambda: st.write(f"{name}, ordering top {vendor} item soon!"))

# Section 7: Know Your Vendor Detailed!
st.markdown("---")
st.markdown("<h2 style='color: #FF1493;'>Know Your Vendor Detailed! 📊</h2>", unsafe_allow_html=True)
vendor = st.selectbox(f"{name}, pick a vendor for a deep dive!", sorted(df['Name'].unique()))  # Show all vendors
vendor_df = df[df['Name'] == vendor]
# Filter by diet preference for consistency
if diet_type == "Veg":
    vendor_df = vendor_df[vendor_df['Food_Type'] == "Veg"]
elif diet_type == "Non-Veg":
    vendor_df = vendor_df[vendor_df['Food_Type'] == "Non-Veg"]
if not vendor_df.empty:
    with st.expander(f"🌟 Detailed Visuals for {vendor} in Madurai! 🍽️", expanded=False):
        # Pie Chart: Dish Distribution by Total Orders
        dish_orders = vendor_df.groupby('Item_Name')['Total_Order'].sum().reset_index()
        fig_pie = px.pie(dish_orders, names='Item_Name', values='Total_Order', title=f"🍵 Dish Popularity at {vendor}")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Bar Chart: Average Rating Distribution
        avg_ratings = vendor_df.groupby('Item_Name')['Avg_Rating'].mean().reset_index()
        fig_bar = px.bar(avg_ratings, x='Item_Name', y='Avg_Rating', title=f"⭐ Ratings for {vendor}'s Dishes")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Histogram: Total Orders per Dish
        fig_hist = px.histogram(vendor_df, x='Total_Order', color='Item_Name', title=f"📈 Orders for {vendor}'s Dishes")
        st.plotly_chart(fig_hist, use_container_width=True)

        # Bar Chart: Price per Item
        price_data = vendor_df.groupby('Item_Name')['Price'].mean().reset_index()
        fig_price_bar = px.bar(price_data, x='Item_Name', y='Price', title=f"💰 Prices for {vendor}'s Dishes",
                               color='Price', color_continuous_scale='Viridis')
        st.plotly_chart(fig_price_bar, use_container_width=True)

# Section 8: Rate the App
st.markdown("---")
st.markdown("<h2 style='color: #FF1493;'>Rate the App! 🌟</h2>", unsafe_allow_html=True)
rating = st.slider("How many stars would you give Sha’s Foodans? (1–5)", 1, 5, 5)
suggestion = st.text_area("Any suggestions or ideas for Sha? Let’s make Madurai tastier together! 🍽️", height=100)
if st.button("Submit Feedback"):
    st.success(f"Thanks, {name}! Your {rating}-star rating and suggestion—'{suggestion}'—mean the world to Sha! 🥰")

# Section 9: Power BI Dashboard (For Internal Use Only)
st.markdown("---")
st.markdown("<h2 style='color: #FF1493;'>Power BI Dashboard (Internal Use Only) 📊</h2>", unsafe_allow_html=True)
power_bi_link = "https://app.powerbi.com/reportEmbed?reportId=118a23f9-e7ab-4f77-bff3-2d878953a342&autoAuth=true&ctid=9a8b1856-f41d-4ec2-aa65-cb2c5d8f5f0e"  # Replace with your actual Power BI publish link
st.markdown(f"""
    <iframe width="100%" height="450" src="{power_bi_link}" frameborder="0" allowFullScreen="true"></iframe>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>Made with ❤️ by Sha for Madurai Foodies!</p>", unsafe_allow_html=True)