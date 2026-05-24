"""
Generate Agent Flow Diagrams
Creates visual representations of Task A and Task B agent graphs
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.task_a_agent import task_a_graph
from backend.agents.task_b_agent import task_b_graph

def generate_flows():
    """Generate and save agent flow diagrams"""
    print("🎨 Generating Agent Flow Diagrams...")
    print("="*60)

    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Task A Flow
        print("\n📊 Generating Task A Agent Flow...")
        task_a_png_path = os.path.join(output_dir, "task_a_agent_flow.png")

        with open(task_a_png_path, "wb") as f:
            f.write(task_a_graph.get_graph().draw_mermaid_png())

        print(f"   ✅ Task A flow saved to: {task_a_png_path}")

        # Task B Flow
        print("\n📊 Generating Task B Agent Flow...")
        task_b_png_path = os.path.join(output_dir, "task_b_agent_flow.png")

        with open(task_b_png_path, "wb") as f:
            f.write(task_b_graph.get_graph().draw_mermaid_png())

        print(f"   ✅ Task B flow saved to: {task_b_png_path}")

        # Also generate Mermaid markdown for documentation
        print("\n📝 Generating Mermaid markdown...")

        mermaid_path = os.path.join(output_dir, "agent_flows.md")
        with open(mermaid_path, "w") as f:
            f.write("# Agent Flow Diagrams\n\n")
            f.write("## Task A Agent - User Modeling\n\n")
            f.write("```mermaid\n")
            f.write(task_a_graph.get_graph().draw_mermaid())
            f.write("\n```\n\n")

            f.write("## Task B Agent - Recommendations\n\n")
            f.write("```mermaid\n")
            f.write(task_b_graph.get_graph().draw_mermaid())
            f.write("\n```\n")

        print(f"   ✅ Mermaid markdown saved to: {mermaid_path}")

        print("\n" + "="*60)
        print("✅ All agent flow diagrams generated successfully!")
        print(f"\nFiles created in '{output_dir}/' directory:")
        print("  - task_a_agent_flow.png")
        print("  - task_b_agent_flow.png")
        print("  - agent_flows.md")

    except Exception as e:
        print(f"\n❌ Error generating flows: {e}")
        print("\nNote: Make sure you have the required dependencies:")
        print("  pip install pygraphviz")
        print("  or")
        print("  pip install pydot")
        raise

if __name__ == "__main__":
    generate_flows()
