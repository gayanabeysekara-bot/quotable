import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PolygonEditor } from "@/components/polygon-editor";

function setup(mode: "area" | "line", draft: [number, number][] = []) {
  const onChange = vi.fn();
  render(<PolygonEditor imageUrl={null} shapes={[]} draft={draft} onDraftChange={onChange} mode={mode} />);
  const canvas = screen.getByTestId("zone-canvas");
  canvas.getBoundingClientRect = () => ({ left: 0, top: 0, width: 200, height: 100, right: 200, bottom: 100, x: 0, y: 0, toJSON: () => ({}) });
  return { canvas, onChange };
}

describe("PolygonEditor", () => {
  it("adds normalised points on click", () => {
    const { canvas, onChange } = setup("area");
    fireEvent.click(canvas, { clientX: 50, clientY: 25 });
    expect(onChange).toHaveBeenCalledWith([[0.25, 0.25]]);
  });

  it("limits entrance boundaries to two points", () => {
    const { canvas, onChange } = setup("line", [[0.1, 0.1], [0.9, 0.9]]);
    fireEvent.click(canvas, { clientX: 10, clientY: 10 });
    expect(onChange).not.toHaveBeenCalled();
  });
});
