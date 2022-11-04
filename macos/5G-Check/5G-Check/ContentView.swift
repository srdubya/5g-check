//
//  ContentView.swift
//  5G-Check
//
//  Created by Steve Wiley on 10/29/22.
//

import SwiftUI

struct ContentView: View {
    @Environment(\.openWindow) private var openWindow
    @EnvironmentObject var gatewayState: GatewayState
    let numCharts = 3.0
    let width = 1.0
    let vMargin = 1.0
    let hSpace = 3.0
    let margin = 1.0
    let numberHeight = NSAttributedString("8").boundingRect(
        with: CGSize(width: 300, height: 300),
        options: [],
        context: nil
    ).height
    let gutter = NSAttributedString("8").boundingRect(
        with: CGSize(width: 300, height: 300),
        options: [],
        context: nil
    ).height
    static let numberFormatter: NumberFormatter = {
        let ret = NumberFormatter()
        ret.numberStyle = .decimal
        ret.usesGroupingSeparator = true
        ret.groupingSeparator = ","
        ret.groupingSize = 3
        return ret
    }()
    static let colors = [
        Color(red: 0.0, green: 0.5, blue: 0.0),
        Color(red: 0.0, green: 0.5, blue: 0.5),
        Color(red: 0.0, green: 0.5, blue: 0.5)
    ]
    
    fileprivate func drawChart(_ size: CGSize, _ context: GraphicsContext, _ chart: ChartData, _ index: Double) {
        let bars = chart.values
        let graphHeight = (((size.height - vMargin) / numCharts) - vMargin - gutter)
        let vOffset = (graphHeight + gutter) * index
        if bars.values.count > 0 {
            let maxBarValue = bars.values.max()!
            let barWidth = ((size.width + hSpace - width) / CGFloat(bars.count)) - (3 * width)
            let scaleFactor = (graphHeight - gutter) / CGFloat(maxBarValue)
            var x = width
            for bar in bars.keys.sorted(by: {a, b in
                if let aAsInt = Int(a) {
                    if let bAsInt = Int(b) {
                        return aAsInt > bAsInt
                    }
                }
                return a > b
            }) {
                let barHeight = scaleFactor * CGFloat(bars[bar]!)
                let barTop = graphHeight - barHeight + vOffset
                context.fill(
                    Path(CGRect(
                        origin: CGPoint(x: x, y: barTop),
                        size: CGSize(width: barWidth, height: barHeight)
                    )),
                    with: .color(ContentView.colors[Int(index)])
                )
                context.draw(
                    Text(ContentView.numberFormatter.string(for: bars[bar]!)!),
                    at: CGPoint(
                        x: x + (barWidth/2),
                        y: barHeight > (numberHeight * 2) ? barTop + numberHeight : barTop - numberHeight)
                )
                context.draw(
                    Text(bar),
                    at: CGPoint(x: x + (barWidth / 2), y: graphHeight + vMargin + (numberHeight/2) + vOffset)
                )
                x += barWidth + hSpace
            }
        }
        context.draw(Text(chart.name).bold(), at: CGPoint(x: width, y: vOffset + numberHeight), anchor: .leading)
    }
    fileprivate func drawCharts(_ size: CGSize, _ context: GraphicsContext) {
        drawChart(size, context, gatewayState.rsrp, 0)
        drawChart(size, context, gatewayState.signal, 1)
        drawChart(size, context, gatewayState.connectionType, 2)
    }
    
    var body: some View {
        VStack(
            alignment: .center,
            spacing: 10
        ) {
            Canvas { context, size in
                drawCharts(size, context)
            }
            HStack {
                TextField("token", text: $gatewayState.token, prompt: Text("auth token string"))
                    .onChange(of: gatewayState.token) { _ in
                        gatewayState.update()
                    }
                Button("Reset", action: {})
            }
        }
        .padding(.all, 4.0)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .frame(width: 300, height: 300)
            .environmentObject(GatewayState(asPreview: true))
    }
}
