"""
This example shows PyRoboPlan capabilities for path planning using a
Probabilistic Roadmap (PRM) algorithm. We rely on a 2-DOF manipulator
to shrink the configuration space so that we can construct a covering
roadmap in reasonable time.
"""

import time

from pinocchio.visualize import MeshcatVisualizer

from pyroboplan.core.utils import get_random_collision_free_state
from pyroboplan.models.two_dof import (
    load_models,
)
from pyroboplan.planning.prm import PRMPlanner, PRMPlannerOptions
from pyroboplan.planning.utils import discretize_joint_space_path


def run_prm_search(q_start, q_end, planner, options):
    for i in range(5):
        print(f"Searching for path attempt: {i+1}...")
        path = planner.plan(q_start, q_end)
        if path:
            break
        else:
            print("Failed to find a path, growing the PRM...")
            planner.construct_roadmap()
            planner.visualize(viz, "ee", show_path=False, show_graph=True)

    # Animate the path
    planner.visualize(viz, "ee", show_path=True, show_graph=True)
    if path:
        input("Press 'Enter' to animate the path.")
        for idx in range(1, len(path)):
            segment_start = path[idx - 1]
            segment_end = path[idx]
            q_path = discretize_joint_space_path(
                segment_start, segment_end, options.max_angle_step
            )
            for q in q_path:
                viz.display(q)
                time.sleep(0.05)


if __name__ == "__main__":
    # Create models and data
    model, collision_model, visual_model = load_models()

    data = model.createData()
    collision_data = collision_model.createData()

    # Initialize visualizer
    viz = MeshcatVisualizer(model, collision_model, visual_model, data=data)
    viz.initViewer(open=True)
    viz.loadViewerModel()

    # Define the start and end configurations
    q_start = get_random_collision_free_state(model, collision_model)
    q_end = get_random_collision_free_state(model, collision_model)
    viz.display(q_start)

    # Configure, initialize, and construct a PRM from scratch
    options = PRMPlannerOptions(
        max_angle_step=0.05,
        max_neighbor_radius=0.25,
        max_neighbor_connections=5,
        max_construction_nodes=2500,
        construction_timeout=10.0,
        prm_file=None,
    )
    planner = PRMPlanner(model, collision_model, options=options)
    print(f"Initializing the roadmap...")
    planner.construct_roadmap()
    planner.visualize(viz, "ee", show_path=False, show_graph=True)

    # We can save the graph to file for use in future PRMs.
    # planner.graph.save_to_file("a.graph")

    while True:
        run_prm_search(q_start, q_end, planner, options)

        # Reusing planners for repeated queries in static environments is one of the
        # key advantages of PRMs.
        input("Press 'Enter' to plan another trajectory, or ctrl-c to quit.")
        planner.reset()
        q_start = q_end
        q_end = get_random_collision_free_state(model, collision_model)
