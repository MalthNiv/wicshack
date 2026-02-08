import { useParams, useNavigate } from "react-router-dom";
import Graph from "../components/Graph";


export default function StockPage() {
 const { symbol } = useParams<{ symbol: string }>();
 const navigate = useNavigate();


 if (!symbol) return null;


 return (
   <div className="stock-page">
     <div className="back-record" onClick={() => navigate("/")}>
       <div className="mini-record">
         <svg className="mini-record-text" viewBox="0 0 100 100">
           <defs>
             <path id="circle-path" d="M 50,50 m -33,0 a 33,33 0 1,1 66,0 a 33,33 0 1,1 -66,0" />
           </defs>
           <text>
             <textPath href="#circle-path" startOffset="0%">
               back to record
             </textPath>
           </text>
         </svg>
         <div className="mini-hole" />
       </div>
     </div>

     <h2>{symbol}</h2>

     <div className="graph-container">
       <Graph symbol={symbol} />
     </div>
   </div>
 );
}

