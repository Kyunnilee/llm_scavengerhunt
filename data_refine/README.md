# Data refine tool
last update: tabi 2024/10/25

## Overview

This tool provides a graph data visualization interface with the following features:

1. **Node and Edge Selection Display**: Select and display specific nodes and edges, with support for batch deletion of nodes or edges.
2. **Add New Nodes**: Add new nodes by specifying latitude and longitude coordinates.
3. **Create New Edges**: Create a new edge between two specified nodes.

## Usage Guide

#### 0. Launch App
`python data_refine/app.py`

#### 1. Display Selected Nodes or Edges
   - Select specific nodes or edges from the interface, with options to display them in the visualization window.
   - After selecting, click the **Refresh** button to update and view the selected results.

#### 2. Delete Nodes or Edges
   - Supports deletion of selected nodes or edges, allowing for batch deletion.
   - After deletion, click **Refresh** to view the updated visualization.

#### 3. Add New Nodes
   - Input the latitude and longitude for a new node, then confirm to add it.
   - After adding the new node, click **Refresh** to display it.

#### 4. Create New Edges
   - Choose two nodes to serve as endpoints for a new edge.
   - After creating the edge, click **Refresh** to update the view.

## Important Notes

- **After selecting new nodes or edges**, click **Refresh** to update the visualization and ensure the selected elements display correctly.
- **After performing delete or add actions**, refresh the view to see the latest visualization results.
- **When handling a large volume of data**, it’s recommended to complete all operations before refreshing to save processing time and ensure a successful update.