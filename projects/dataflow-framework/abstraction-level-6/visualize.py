from pipeline import build_routing, visualize_routing

nodes = build_routing("pipeline.yaml")
visualize_routing(nodes, output_file="routing_graph.png")
