import tkinter as tk
from tkinter import filedialog, simpledialog
import geopandas as gpd
import folium
import webview
import time
import heapq


class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Road Network UI")

        self.roads_shp = None
        self.nodes_shp = None
        self.origin_node = None
        self.destination_node = None
        self.adjacency_matrix = {}

        self.create_widgets()

    def create_widgets(self):
        tk.Button(self.root, text="Choose Roads File", command=self.load_roads).pack(pady=5)
        tk.Button(self.root, text="Choose Nodes File", command=self.load_nodes).pack(pady=5)
        tk.Button(self.root, text="Enter Origin Node", command=self.enter_origin).pack(pady=5)
        tk.Button(self.root, text="Enter Destination Node", command=self.enter_destination).pack(pady=5)
        tk.Button(self.root, text="Find Fastest Paths", command=self.find_fastest_paths).pack(pady=5)

    def load_roads(self):
        file_path = filedialog.askopenfilename(filetypes=[("Shapefiles", "*.shp")])
        if file_path:
            start_time = time.time()
            self.roads_shp = gpd.read_file(file_path)
            self.roads_shp = self.roads_shp.to_crs(epsg=4326)  # Ensure coordinates are in WGS84
            print(f"Loading and transforming roads shapefile took {time.time() - start_time:.4f} seconds")
            self.create_adjacency_matrix()

    def load_nodes(self):
        file_path = filedialog.askopenfilename(filetypes=[("Shapefiles", "*.shp")])
        if file_path:
            start_time = time.time()
            self.nodes_shp = gpd.read_file(file_path)
            self.nodes_shp = self.nodes_shp.to_crs(epsg=4326)  # Ensure coordinates are in WGS84
            print(f"Loading and transforming nodes shapefile took {time.time() - start_time:.4f} seconds")

    def create_adjacency_matrix(self):
        if self.roads_shp is not None:
            start_time = time.time()
            self.adjacency_matrix = {}

            for _, row in self.roads_shp.iterrows():
                from_node = row["from"]
                to_node = row["to"]
                time_weight = row["Time"]

                if from_node not in self.adjacency_matrix:
                    self.adjacency_matrix[from_node] = {}
                if to_node not in self.adjacency_matrix:
                    self.adjacency_matrix[to_node] = {}

                self.adjacency_matrix[from_node][to_node] = time_weight

                # Add reverse edge if the road is bidirectional
                if row["oneway"] == 0:
                    self.adjacency_matrix[to_node][from_node] = time_weight

            print(f"Adjacency matrix creation took {time.time() - start_time:.4f} seconds")

    def enter_origin(self):
        self.origin_node = self.get_node_input("Enter Origin Node osmid:")
        if self.origin_node is not None:
            print(f"Origin node selected: {self.origin_node}")

    def enter_destination(self):
        self.destination_node = self.get_node_input("Enter Destination Node osmid:")
        if self.destination_node is not None:
            print(f"Destination node selected: {self.destination_node}")

    def get_node_input(self, prompt):
        if self.nodes_shp is None:
            print("Please load the nodes shapefile first.")
            return None

        try:
            node_id = simpledialog.askstring("Input", prompt)
            if node_id is None:
                return None  # User canceled the input

            node_id = int(node_id)

            if node_id not in self.nodes_shp["osmid"].values:
                print(f"Node with osmid {node_id} not found.")
                return None

            return node_id

        except ValueError:
            print("Invalid input. Please enter a valid osmid (integer).")
            return None

    def find_fastest_paths(self):
        if self.origin_node is None or self.destination_node is None:
            print("Please specify both origin and destination nodes.")
            return

        if not self.adjacency_matrix:
            print("Adjacency matrix not created yet. Load the road shapefile.")
            return

        start_time = time.time()
        paths = self.k_shortest_paths(self.origin_node, self.destination_node, k=3)

        if not paths:
            print("No paths found between the selected nodes.")
        else:
            for i, (path, total_time) in enumerate(paths):
                print(f"Path {i + 1}: {path} with total time {total_time:.2f} minutes")
            self.display_paths(paths)


    def dijkstra(self, start, end):
        pq = [(0, start, [])]  # Priority queue: (cumulative cost, current node, path)
        visited = set()

        while pq:
            current_cost, current_node, path = heapq.heappop(pq)

            if current_node in visited:
                continue

            visited.add(current_node)
            path = path + [current_node]

            if current_node == end:
                return path, current_cost

            for neighbor, weight in self.adjacency_matrix.get(current_node, {}).items():
                if neighbor not in visited:
                    heapq.heappush(pq, (current_cost + weight, neighbor, path))

        return None, float('inf')

    def k_shortest_paths(self, start, end, k=3):
        """
        Compute the k-shortest paths using a variation of Dijkstra's algorithm.
        Avoid edges that would result in loops if they are not in the fastest path.
        """
        paths = []
        pq = [(0, start, [])]  # Priority queue: (cumulative cost, current node, path)
        excluded_edges = set()  # Edges to be excluded for subsequent paths

        while pq and len(paths) < k:
            current_cost, current_node, path = heapq.heappop(pq)

            if path and path[-1] == end:
                # Record the completed path
                paths.append((path, current_cost))
                # Identify excluded edges from the fastest path (first path)
                if len(paths) == 1:  # Only for the fastest path
                    fastest_path_edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
                    for edge in fastest_path_edges:
                        if edge not in excluded_edges:
                            excluded_edges.add(edge)  # Exclude edge
                            # Also exclude the edge immediately following it
                            for next_edge in fastest_path_edges:
                                if edge[1] == next_edge[0]:  # Edge continuation
                                    excluded_edges.add(next_edge)
                continue

            for neighbor, weight in self.adjacency_matrix.get(current_node, {}).items():
                if neighbor not in path:  # Avoid cycles
                    edge = (current_node, neighbor)
                    if edge not in excluded_edges:
                        heapq.heappush(pq, (current_cost + weight, neighbor, path + [neighbor]))

        return paths

    def display_paths(self, paths):
        start_time = time.time()
        m = folium.Map(location=(32.0797, 34.7628), zoom_start=13)

        # Define colors for the paths
        colors = ["red", "blue", "green"]  # Green for third, Blue for second, Red for fastest

        # Store total HUMRAT_TEU for each path
        path_risks = []

        # Draw the paths in reverse order (third, second, fastest)
        for i, (path, total_time) in enumerate(paths[::-1]):
            path_index = len(paths) - i - 1  # Adjust index to match reversed order
            color = colors[path_index]

            # Extract edges for the path
            path_edges = [(path[j], path[j + 1]) for j in range(len(path) - 1)]
            path_lines = self.roads_shp[
                self.roads_shp.apply(
                    lambda row: (row["from"], row["to"]) in path_edges or (row["to"], row["from"]) in path_edges, axis=1
                )
            ]

            # Calculate total HUMRAT_TEU for this path
            total_risk = path_lines["HUMRAT_TEU"].sum()
            path_risks.append((path_index + 1, total_risk))  # Save path index and risk

            # Add the path to the map
            folium.GeoJson(
                path_lines,
                style_function=lambda x, color=color: {
                    "color": color,
                    "weight": 5  # Keep the line width consistent
                },
                name=f"Path {path_index + 1}"
            ).add_to(m)

        # Rank paths by safety (lowest total HUMRAT_TEU first)
        path_risks.sort(key=lambda x: x[1])  # Sort by total_risk (HUMRAT_TEU)

        # Create safety text
        safety_text_html = """
        <div style="position: absolute; top: 120px; left: 10px; background-color: white; padding: 10px; border-radius: 5px;">
            <strong>Safety Ranking:</strong><br>
            <span style="color: {}; font-weight: bold;">The safest path: Path {}</span><br>
            <span style="color: {}; font-weight: bold;">Path {} is {:.2f}% more dangerous</span><br>
            <span style="color: {}; font-weight: bold;">Path {} is {:.2f}% more dangerous</span>
        </div>
        """.format(
            colors[path_risks[0][0] - 1], path_risks[0][0],
            colors[path_risks[1][0] - 1], path_risks[1][0],
            ((path_risks[1][1] - path_risks[0][1]) / path_risks[0][1]) * 100,
            colors[path_risks[2][0] - 1], path_risks[2][0],
            ((path_risks[2][1] - path_risks[0][1]) / path_risks[0][1]) * 100
        )
        print(f"Displaying paths and saving the map took {time.time() - start_time:.4f} seconds")
        # Add the safety ranking text as a marker on the map
        folium.Marker(
            location=(32.0797, 34.7528),  # Adjust position as needed
            icon=folium.DivIcon(html=safety_text_html)
        ).add_to(m)

        # Add the timing text
        time_text_html = """
        <div style="position: absolute; top: 10px; left: 10px; background-color: white; padding: 10px; border-radius: 5px;">
            <strong>Path Times:</strong><br>
            <span style="color: red;">Fastest path: {:.2f} min</span><br>
            <span style="color: blue;">Second: {:.2f} min</span><br>
            <span style="color: green;">Third: {:.2f} min</span>
        </div>
        """.format(paths[0][1], paths[1][1], paths[2][1])

        # Add the timing text as a marker on the map
        folium.Marker(
            location=(32.0797, 34.7628),  # Adjust position as needed
            icon=folium.DivIcon(html=time_text_html)
        ).add_to(m)

        folium.LayerControl().add_to(m)
        m.save("map.html")


        webview.create_window("Paths Map", "map.html")
        webview.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
