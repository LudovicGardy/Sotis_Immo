import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import numpy as np

from utils.calculs import calculate_median_difference
from .config import data_URL
data_gouv_dict = data_URL()

# 🏠 Pour une vision plus actuelle, sélectionnez l'année 2024. Vous obtiendrez ainsi une approximation en temps quasi-réel 
#             des valeurs de plusieurs dizaines de milliers de biens actuellement sur le marché. Veuillez noter que les données 
#             concernant les ventes réalisées en 2024 ne seront disponibles qu'à partir de 2024.

class Plotter:

    def __init__(self):
        print('Initializing Plotter...')

    def create_plots(self):
        '''
        Create the plots.

        Parameters
        ----------
        None

        Returns
        -------
        Grphical representation
        '''

        if self.df_pandas is None:
            st.error("Pas d'information disponible pour le département {} en {}. Sélectionnez une autre configuration.".format(self.selected_department, self.selected_year))
            return

        # Set the title of the section
        # st.markdown('# Sotis A.I. Immobilier')
        st.markdown('## Visualisez les prix de l\'immobilier en France')
        st.markdown(f"""
        🏠 Les graphiques interactifs que vous découvrirez ci-dessous offrent une vue d'ensemble détaillée des valeurs immobilières 
                    en France, réparties par type de bien : maisons, appartements et locaux commerciaux. Grâce à la barre d'options 
                    latérale, personnalisez votre expérience en sélectionnant le département, l'année et la catégorie de bien qui vous 
                    intéressent. Vous aurez ainsi accès à un riche ensemble de données portant sur plusieurs millions de transactions 
                    immobilières effectuées entre {data_gouv_dict.get('data_gouv_years')[0]} et {data_gouv_dict.get('data_gouv_years')[-1]}.
        """)

        ### Section 1
        if "Carte" in self.selected_plots:
            # Afficher l'alerte si l'année sélectionnée est 2024
            if f"{data_gouv_dict.get('data_gouv_years')[-1]+1}" in self.selected_year:
                st.warning(f"""⚠️ Les tarifs pour {data_gouv_dict.get('data_gouv_years')[-1]+1} sont mis à jour régulièrement par le robot Sotis-IMMO 🤖.
                              À la différence des données de {data_gouv_dict.get('data_gouv_years')[0]}-{data_gouv_dict.get('data_gouv_years')[-1]}, qui concernent des biens déjà vendus, celles de {data_gouv_dict.get('data_gouv_years')[-1]+1} présentent 
                              les offres en quasi temps-réel. Toutefois, elles sont moins précises sur le plan géographique, 
                              étant regroupées par zones approximatives, contrairement aux données des années précédentes, qui sont 
                              présentées par adresse.""")
                
            if 'selected_postcode_title' in st.session_state and st.session_state.selected_postcode_title:
                map_title = f"Distribution des prix médians pour les {self.selected_property_type.lower()}s dans le {st.session_state.selected_postcode_title} en {self.selected_year}"
            else:
                map_title = f"Distribution des prix médians pour les {self.selected_property_type.lower()}s dans le {self.selected_department} en {self.selected_year}"
            st.markdown(f"### {map_title}")
            self.plot_map()
            st.divider()

        ### Section 2
        if "Fig. 1" in self.selected_plots:
            st.markdown(f"### Fig 1. Distribution des prix médians dans le {self.selected_department} en {self.selected_year}")
            self.plot_1()
            st.divider()

        ### Section 3
        if "Fig. 2" in self.selected_plots:
            st.markdown(f"### Fig 2. Distribution des prix médians pour les {self.selected_property_type.lower()}s dans le {self.selected_department} en {self.selected_year}")
            st.markdown("""Les nombres au-dessus des barres représentent le nombre de biens par code postal. 
                        Ils fournissent un contexte sur le volume des ventes pour chaque zone.""")
            self.plot_2()
            st.divider()

        ### Section 4
        if "Fig. 3" in self.selected_plots:
            st.markdown(f"""### Fig 3. Evolution des prix médians des {self.selected_property_type.lower()}s dans le {self.selected_department} entre {data_gouv_dict.get('data_gouv_years')[0]} et {data_gouv_dict.get('data_gouv_years')[-1]}""")
            if f"{data_gouv_dict.get('data_gouv_years')[-1]+1}" in self.selected_year:
                st.warning(f"""La figure 3 ne peut pas encore s'étendre à {data_gouv_dict.get('data_gouv_years')[-1]+1} et 
                           s'arrête à {data_gouv_dict.get('data_gouv_years')[-1]}. Une mise à jour sera publiée prochainement.""")
            self.plot_3()
            st.divider()

        ### Section 5
        if "Fig. 4" in self.selected_plots:
            st.markdown(f"### Fig 4. Distribution des prix unitaires (par bien) dans votre quartier en {self.selected_year}")
            self.plot_4()

    def plot_map(self):

        col1, col2 = st.columns(2)  # Créer deux colonnes

        with col2:
            mapbox_styles = ["open-street-map", "carto-positron", "carto-darkmatter", "white-bg"]
            default_map = mapbox_styles.index("open-street-map")
            self.selected_mapbox_style = st.selectbox("🌏 Style de carte", mapbox_styles, index=default_map)

            colormaps = ["Rainbow", "Portland", "Jet", "Viridis", "Plasma", "Cividis", "Inferno", "Magma", "RdBu"]
            default_cmap = colormaps.index("Rainbow")
            self.selected_colormap = st.selectbox("🎨 Echelle de couleurs", colormaps, index=default_cmap)

        with col1:
            self.use_fixed_marker_size = st.checkbox("Fixer la taille des points", False)

            self.use_jitter = st.checkbox("Eviter la superposition des points", True)
            self.jitter_value = 0 #0.001       

            self.remove_outliers = st.checkbox("Supprimer les valeurs extrêmes", True)
            st.caption("""Retirer les valeurs extrêmes (>1.5*IQR) permet d'améliorer la lisibilité de la carte.
                       Ces valeurs sont éliminées uniquement sur cette représentation, pas les prochaine.""")

        if self.selected_year == data_gouv_dict.get('data_gouv_years')[-1]+1 and not self.use_jitter:
            st.success(f"""💡 Pour une meilleure visibilité des données géographiques de {data_gouv_dict.get('data_gouv_years')[-1]+1}, il est conseillé de cocher la case
                        'Eviter la superposition des points' ci-dessus.""")

        # Filtring the dataframe by property type
        filtered_df = self.df_pandas[self.df_pandas['type_local'] == self.selected_property_type]
        
        # Further filtering if a postcode is selected
        if hasattr(st.session_state, 'selected_postcode'):
            filtered_df = filtered_df[filtered_df['code_postal'] == st.session_state.selected_postcode]

        if self.remove_outliers:
            # Calculate Q1, Q3, and IQR
            Q1 = filtered_df['valeur_fonciere'].quantile(0.25)
            Q3 = filtered_df['valeur_fonciere'].quantile(0.75)
            IQR = Q3 - Q1
            # Calculate the upper fence (using 1.5xIQR)
            upper_fence = Q3 + 1.5 * IQR
            # Filter out outliers based on the upper fence
            filtered_df = filtered_df[filtered_df['valeur_fonciere'] <= upper_fence]

        # (Optional) Jittering : add a small random value to the coordinates to avoid overlapping markers
        if int(self.selected_year.split(" ")[-1]) == {data_gouv_dict.get('data_gouv_years')[-1]+1}:
            val = 0.1
        else:
            val = 0 #0.001

        self.jitter_value = val if self.use_jitter else 0
        filtered_df['longitude'] = filtered_df['longitude'].astype(float)
        filtered_df['latitude'] = filtered_df['latitude'].astype(float)
        filtered_df.loc[:, 'latitude'] = filtered_df['latitude'] + np.random.uniform(-self.jitter_value, self.jitter_value, size=len(filtered_df))
        filtered_df.loc[:, 'longitude'] = filtered_df['longitude'] + np.random.uniform(-self.jitter_value, self.jitter_value, size=len(filtered_df))
        
        # Add a column with a fixed size for all markers
        filtered_df = filtered_df.assign(marker_size=0.5)

        size_column = 'marker_size' if self.use_fixed_marker_size else 'valeur_fonciere'

        # Create the map
        fig = px.scatter_mapbox(filtered_df, 
                                lat='latitude', 
                                lon='longitude', 
                                color='valeur_fonciere', 
                                size=size_column, 
                                color_continuous_scale=self.selected_colormap, 
                                size_max=15, 
                                zoom=6, 
                                opacity=0.8, 
                                hover_data=['code_postal', 'valeur_fonciere', 'longitude', 'latitude'])
                        
        # Update the map style
        fig.update_layout(mapbox_style=self.selected_mapbox_style)
        fig.update_coloraxes(colorbar_thickness=10, colorbar_title_text="", colorbar_x=1, colorbar_xpad=0, colorbar_len=1.0, colorbar_y=0.5)
        fig.update_layout(height=800)

        st.plotly_chart(fig, use_container_width=True)

    def plot_1(self):
        grouped_data = self.df_pandas.groupby(["code_postal", "type_local"]).agg({
            "valeur_fonciere": "median"
        }).reset_index()

        # Triez grouped_data par code_postal
        grouped_data = grouped_data.sort_values("code_postal")

        # Réinitialisez l'index de grouped_data
        grouped_data = grouped_data.reset_index(drop=True)

        
        fig = px.line(grouped_data, x=grouped_data.index, y='valeur_fonciere', color='type_local', 
                    markers=True, labels={'valeur_fonciere': 'Average Price'})

        # Utilisez l'index pour tickvals et les codes postaux pour ticktext
        tickvals = grouped_data.index[::len(grouped_data['type_local'].unique())]
        ticktext = grouped_data['code_postal'].unique()
        
        # Utilisez tickvals et ticktext pour mettre à jour l'axe des x
        fig.update_xaxes(tickvals=tickvals, ticktext=ticktext, range=[tickvals[0], tickvals[-1]], title_text = "Code postal")
        fig.update_yaxes(title_text='Prix médian en €')
        fig.update_layout(legend_orientation="h", 
                        legend=dict(y=1.1, x=0.5, xanchor='center', title_text=''),
                        height=600)
        st.plotly_chart(fig, use_container_width=True)

    def plot_2(self):

        # Check for orientation preference
        orientation = st.radio("Orientation", ["Barres horizontales (Grand écran)", "Barres verticales (Petit écran)"], label_visibility="hidden")

        # Filtring the dataframe by property type
        filtered_df = self.df_pandas[self.df_pandas['type_local'] == self.selected_property_type]

        # Grouping the dataframe by postal code and calculating the average property price
        grouped = filtered_df.groupby('code_postal').agg({
            'valeur_fonciere': 'median',
            'type_local': 'count'
        }).reset_index()

        # Renaming the columns
        grouped.columns = ['Postal Code', 'Property Value', 'Count']

        # Creation of the bar chart
        if orientation == "Barres horizontales (Grand écran)":
            fig = px.bar(grouped, x='Postal Code', y='Property Value')
            fig.update_layout(yaxis_title='Prix médian en €', xaxis_title='Code postal')
            fig.update_yaxes(type='linear')
            fig.update_xaxes(type='category')
            fig.update_layout(height=600)
        else:
            fig = px.bar(grouped, y='Postal Code', x='Property Value', orientation='h')
            fig.update_layout(xaxis_title='Prix médian en €', yaxis_title='Code postal')
            fig.update_yaxes(type='category')
            fig.update_xaxes(type='linear')
            fig.update_layout(height=1200)

        # Update the bar chart
        fig.update_traces(text=grouped['Count'], textposition='outside')
        st.plotly_chart(fig, use_container_width=True)



    def plot_3(self):

        # Add a selectbox for choosing between bar and line plot
        #plot_types = ["Bar", "Line"]
        #selected_plot_type = st.selectbox("Selectionner une visualisation", plot_types, index=0)

        selected_plot_type = st.radio("Type", ["Graphique en barres", "Graphique en lignes"], label_visibility="hidden")

        # Determine the column to display
        value_column = 'Median Value SQM' if self.normalize_by_area else 'Median Value'

        # Filter the dataframe by the provided department code
        dept_data = self.summarized_df_pandas[self.summarized_df_pandas['code_departement'] == self.selected_department]

        # Generate a brighter linear color palette
        years = sorted(dept_data['Year'].unique())
        property_types = dept_data['type_local'].unique()

        # Liste des couleurs bleues
        blue_palette = ['#08519c', '#3182bd', '#6baed6', '#bdd7e7', '#eff3ff', '#ffffff']

        # Assurez-vous que le nombre de couleurs dans la palette correspond au nombre d'années
        if len(blue_palette) != len(years):
            st.error("Le nombre de couleurs dans la palette ne correspond pas au nombre d'années.")
            return

        if selected_plot_type == "Graphique en barres":
            cols = st.columns(len(property_types))

            # Associez chaque année à une couleur
            year_to_color = dict(zip(sorted(years), blue_palette))            

            for idx, prop_type in enumerate(property_types):
                annual_average_diff, percentage_diff = calculate_median_difference(self.summarized_df_pandas, self.selected_department, self.normalize_by_area, prop_type)
                with cols[idx]:
                    if annual_average_diff > 0:
                        st.metric(label=prop_type, value=f"+{annual_average_diff:.2f} € / an", delta=f"{percentage_diff:.2f} % depuis 2018")
                    else:
                        st.metric(label=prop_type, value=f"{annual_average_diff:.2f} € / an", delta=f"{percentage_diff:.2f} % depuis 2018")

                    prop_data = dept_data[dept_data['type_local'] == prop_type]
                    
                    # Créez une liste pour stocker les tracés
                    traces = []
                    for year in prop_data['Year'].unique():
                        year_data = prop_data[prop_data['Year'] == year]
                        traces.append(go.Bar(x=year_data['Year'], y=year_data[value_column], name=str(year), marker_color=year_to_color[year]))
                    
                    layout = go.Layout(barmode='group', height=400, showlegend=False)

                    fig = go.Figure(data=traces, layout=layout)
                    st.plotly_chart(fig, use_container_width=True)

                    
        else:

            cols = st.columns(len(property_types))

            for idx, prop_type in enumerate(property_types):

                annual_average_diff, percentage_diff = calculate_median_difference(self.summarized_df_pandas, self.selected_department, self.normalize_by_area, prop_type)

                with cols[idx]:
                    if annual_average_diff > 0:
                        st.metric(label=prop_type, value=f"+{annual_average_diff:.2f} € / an", delta=f"{percentage_diff:.2f} % depuis 2018")
                    else:
                        st.metric(label=prop_type, value=f"{annual_average_diff:.2f} € / an", delta=f"{percentage_diff:.2f} % depuis 2018")

            fig = px.line(dept_data, 
                          x='Year', 
                          y=value_column, 
                          color='type_local',
                          labels={"median_value": "Prix médian en €", "Year": "Année"},
                          markers=True,
                          height=600)

            fig.update_layout(xaxis_title="Type de bien",
                              yaxis_title="Prix médian en €",
                              legend_title="Type de bien",
                              height=600)
            fig.update_layout(legend_orientation="h", 
                            legend=dict(y=1.1, x=0.5, xanchor='center', title_text=''))
            
            st.plotly_chart(fig, use_container_width=True)


    def plot_4(self):

        unique_postcodes = self.df_pandas['code_postal'].unique()
                
        ### Set up the postal code selectbox and update button
        selected_postcode = st.selectbox("Code postal", sorted(unique_postcodes))

        # col1, col2 = st.columns([1,3])
        # with col1:
        #     if st.button(f"🌏 Actualiser la carte pour {selected_postcode}"):
        #         st.session_state.selected_postcode = selected_postcode
        #         st.session_state.selected_postcode_title = selected_postcode
        #         st.experimental_rerun()
        # with col2:
        #     st.caption("""**'Actualiser la carte'** sert à rafraîchir la carte, tout en haut de la fenêtre, pour afficher les 
        #                données de votre quartier spécifiquement au lieu d'afficher tout le département.""")
            

        # Si le bouton est cliqué, mettez à jour la carte avec les données du code postal sélectionné
        filtered_by_postcode = self.df_pandas[self.df_pandas['code_postal'] == selected_postcode]

        unique_property_types = filtered_by_postcode['type_local'].unique()

        # Créer le nombre approprié de colonnes
        cols = st.columns(len(unique_property_types))

        color_palette = sns.color_palette('tab10', len(unique_property_types)).as_hex()
        colors = dict(zip(unique_property_types, color_palette))

        for idx, property_type in enumerate(unique_property_types):

            subset = filtered_by_postcode[filtered_by_postcode['type_local'] == property_type]
            trace = go.Box(y=subset['valeur_fonciere'], 
                        name=property_type, 
                        marker_color=colors[property_type], 
                        boxpoints='all', 
                        jitter=0.3, 
                        pointpos=0, 
                        marker=dict(opacity=0.5))

            fig = go.Figure(data=[trace])
            fig.update_layout(yaxis_title='Prix médian en €')
            fig.update_layout(height=600)
            fig.update_layout(legend_orientation="h", legend=dict(y=1.1, x=0.5, xanchor='center'))
            fig.update_layout(margin=dict(t=20, b=80, l=50, r=50))
            
            # Retirer les labels des x
            fig.update_xaxes(showticklabels=False)

            # Ajoutez un titre en utilisant st.markdown() avant d'afficher le graphique
            with cols[idx]:
                st.markdown(f"<div style='text-align: center;'>{property_type}</div>", unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)